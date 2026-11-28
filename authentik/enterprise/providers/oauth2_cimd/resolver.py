"""Resolve public client ID URLs into validated, cached client records.

- Admission runs first, on every call, before anything is read or fetched.
  Together with the TTL it bounds what the cache can hold.
- Entries live in the shared Django cache (PostgreSQL in authentik), so all
  workers share them. Each holds the parsed document, re-validated on every
  read, so validation changes apply to existing entries.
- An entry is fresh for its HTTP freshness lifetime (60 s to 5 min). After that
  it's refetched; if the refetch fails transiently, the last valid document is
  served as `stale` for up to an hour, retrying at most once a minute (draft -03
  section 6.1). Terminal failures, including a `client_id` mismatch, purge it.
  Failures and invalid documents are never cached (draft -03 section 6.2).
- Concurrent resolutions of one client in a process share one fetch. There is
  no cross-worker coordination: each worker fetches at most once per freshness
  lifetime per admitted client.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from time import monotonic, time
from typing import Any

from django.core.cache import BaseCache, cache
from structlog.stdlib import get_logger

from authentik.enterprise.providers.oauth2_cimd.bounded_json import (
    is_json_media_type,
    parse_json_object,
)
from authentik.enterprise.providers.oauth2_cimd.client import CIMDClient
from authentik.enterprise.providers.oauth2_cimd.constants import (
    LOG_CLIENT_ID_LENGTH,
    METADATA_MAX_BYTES,
    STALE_IF_ERROR,
    STALE_RETRY_INTERVAL,
)
from authentik.enterprise.providers.oauth2_cimd.errors import (
    CIMDError,
    ClientNotAdmitted,
    InvalidClientMetadata,
    MetadataRejected,
    MetadataUnavailable,
)
from authentik.enterprise.providers.oauth2_cimd.freshness import freshness
from authentik.enterprise.providers.oauth2_cimd.metadata import (
    ClientMetadata,
    parse_client_id,
    validate_metadata,
)
from authentik.enterprise.providers.oauth2_cimd.metrics import (
    COUNTER_CIMD_CACHE,
    COUNTER_CIMD_RESOLVE,
    HIST_CIMD_FETCH,
)
from authentik.lib.utils.untrusted_fetch import (
    BlockedDestination,
    InvalidURL,
    RedirectNotAllowed,
    ResponseTooLarge,
    UnexpectedStatus,
    UnsupportedContentEncoding,
    UntrustedFetchError,
    UntrustedURLFetcher,
    get_untrusted_fetcher,
)

LOGGER = get_logger()

CACHE_PREFIX = "goauthentik.io/enterprise/providers/oauth2_cimd/metadata"
ENTRY_VERSION = 1
METADATA_ACCEPT = "application/json"
# How long concurrent callers wait for a shared fetch, on top of the fetcher's deadline
FLIGHT_MARGIN = 2.0
# Fetch errors that retrying won't fix (draft -03 section 6.1 "terminal" failures)
_TERMINAL_FETCH_ERRORS = (
    InvalidURL,
    BlockedDestination,
    RedirectNotAllowed,
    ResponseTooLarge,
    UnsupportedContentEncoding,
)
# 4xx statuses that are transient: request timeout and rate limiting
_TRANSIENT_STATUSES = frozenset((408, 429))

# Called with the client ID. Returns False if the client isn't admitted.
Admit = Callable[[str], bool]


def log_client_id(client_id: object) -> str:
    """A client ID shortened for log events"""
    value = client_id if isinstance(client_id, str) else repr(client_id)
    if len(value) <= LOG_CLIENT_ID_LENGTH:
        return value
    return value[:LOG_CLIENT_ID_LENGTH] + "..."


@dataclass(frozen=True, slots=True)
class _Entry:
    """A cached valid document"""

    document: dict[str, Any]
    fetched_at: float
    # Fresh until `expires_at`; usable on transient failures until `stale_until`
    expires_at: float
    stale_until: float
    # After a transient failure, no refetch is attempted before `retry_at`
    retry_at: float = 0.0

    def to_cache(self) -> dict[str, Any]:
        return {
            "version": ENTRY_VERSION,
            "document": self.document,
            "fetched_at": self.fetched_at,
            "expires_at": self.expires_at,
            "stale_until": self.stale_until,
            "retry_at": self.retry_at,
        }

    @classmethod
    def from_cache(cls, value: Any) -> _Entry | None:
        if not isinstance(value, dict) or value.get("version") != ENTRY_VERSION:
            return None
        try:
            return cls(
                document=value["document"],
                fetched_at=float(value["fetched_at"]),
                expires_at=float(value["expires_at"]),
                stale_until=float(value["stale_until"]),
                retry_at=float(value["retry_at"]),
            )
        except KeyError, TypeError, ValueError:
            return None


class _Flight:
    """A fetch in progress in this process, shared by concurrent callers"""

    def __init__(self) -> None:
        self.done = threading.Event()
        self.result: _Entry | None = None
        self.error: CIMDError | None = None
        self.waiters = 0


class PublicClientResolver:
    """Fetch, validate and cache public client metadata documents.

    Use the module-level `resolve_public_client()`; instances are for tests."""

    def __init__(
        self,
        *,
        cache_backend: BaseCache | None = None,
        fetcher: UntrustedURLFetcher | None = None,
        clock: Callable[[], float] = time,
    ):
        self._cache_backend = cache_backend
        self._fetcher = fetcher
        self._clock = clock
        self._flights: dict[str, _Flight] = {}
        self._flights_lock = threading.Lock()

    @property
    def _cache(self) -> BaseCache:
        return self._cache_backend if self._cache_backend is not None else cache

    def resolve(self, client_id: str, *, admit: Admit) -> CIMDClient:
        """Resolve `client_id` as a public client.

        `admit` runs first, on every call including cache hits. Raises a
        CIMDError subclass."""
        try:
            parse_client_id(client_id)
            if not admit(client_id):
                raise ClientNotAdmitted("not_admitted", "Client is not admitted")
            client = self._resolve(client_id)
        except CIMDError as exc:
            COUNTER_CIMD_RESOLVE.labels(outcome=exc.reason).inc()
            LOGGER.debug(
                "CIMD client rejected",
                client_id=log_client_id(client_id),
                reason=exc.reason,
                code=exc.code,
            )
            raise
        COUNTER_CIMD_RESOLVE.labels(outcome="stale" if client.stale else "success").inc()
        return client

    def invalidate(self, client_id: str) -> None:
        """Drop the cached document of `client_id` on all workers.

        A fetch already in flight when this runs may still store its result."""
        self._cache.delete(self._key(client_id))

    # Resolution

    def _resolve(self, client_id: str) -> CIMDClient:
        key = self._key(client_id)
        now = self._clock()
        entry = _Entry.from_cache(self._cache.get(key))
        metadata: ClientMetadata | None = None
        if entry is not None:
            try:
                metadata = validate_metadata(entry.document, client_id)
            except CIMDError:
                # Validation became stricter since the entry was written
                self._cache.delete(key)
                entry = None
        if entry is not None and metadata is not None:
            if now < entry.expires_at:
                COUNTER_CIMD_CACHE.labels(result="hit").inc()
                return metadata.to_client(expires_at=entry.expires_at, stale=False)
            if now < min(entry.retry_at, entry.stale_until):
                COUNTER_CIMD_CACHE.labels(result="stale").inc()
                return metadata.to_client(expires_at=entry.retry_at, stale=True)
        COUNTER_CIMD_CACHE.labels(result="miss" if entry is None else "expired").inc()
        try:
            fetched = self._load(client_id, key)
        except CIMDError as exc:
            if not exc.transient:
                # A terminal failure ends trust in the previous document
                self._cache.delete(key)
                raise
            if entry is None or metadata is None or now >= entry.stale_until:
                raise
            return self._serve_stale(client_id, key, entry, metadata, exc)
        return validate_metadata(fetched.document, client_id).to_client(
            expires_at=fetched.expires_at, stale=False
        )

    def _serve_stale(
        self,
        client_id: str,
        key: str,
        entry: _Entry,
        metadata: ClientMetadata,
        exc: CIMDError,
    ) -> CIMDClient:
        now = self._clock()
        retry_at = min(now + STALE_RETRY_INTERVAL, entry.stale_until)
        backoff = _Entry(
            document=entry.document,
            fetched_at=entry.fetched_at,
            expires_at=entry.expires_at,
            stale_until=entry.stale_until,
            retry_at=retry_at,
        )
        self._store(key, backoff)
        LOGGER.warning(
            "CIMD metadata refetch failed, using last valid document",
            client_id=log_client_id(client_id),
            reason=exc.reason,
            code=exc.code,
            stale_for=round(now - entry.expires_at),
        )
        return metadata.to_client(expires_at=retry_at, stale=True)

    # Cache

    @staticmethod
    def _key(client_id: str) -> str:
        return f"{CACHE_PREFIX}/{sha256(client_id.encode()).hexdigest()}"

    def _store(self, key: str, entry: _Entry) -> None:
        # Backend expiry has second granularity; the entry's own times stay authoritative
        timeout = int(entry.stale_until - self._clock()) + 1
        if timeout > 0:
            self._cache.set(key, entry.to_cache(), timeout=timeout)

    # Fetching

    def _fetcher_instance(self) -> UntrustedURLFetcher:
        return self._fetcher or get_untrusted_fetcher()

    def _load(self, client_id: str, key: str) -> _Entry:
        """Fetch, validate and store the document, sharing one fetch between concurrent callers"""
        with self._flights_lock:
            flight = self._flights.get(client_id)
            leader = flight is None
            if flight is None:
                flight = self._flights[client_id] = _Flight()
            else:
                flight.waiters += 1
        if not leader:
            if not flight.done.wait(self._fetcher_instance().timeout + FLIGHT_MARGIN):
                raise MetadataUnavailable("flight_timeout", "Timed out waiting for fetch")
            if flight.error is not None:
                raise type(flight.error)(flight.error.code, str(flight.error))
            if flight.result is None:
                raise MetadataUnavailable("flight_failed", "Concurrent fetch failed")
            return flight.result
        try:
            flight.result = self._fetch(client_id, key)
            return flight.result
        except CIMDError as exc:
            flight.error = exc
            raise
        finally:
            with self._flights_lock:
                self._flights.pop(client_id, None)
            flight.done.set()

    def _fetch(self, client_id: str, key: str) -> _Entry:
        started = monotonic()
        requested_at = self._clock()
        outcome = "success"
        try:
            try:
                response = self._fetcher_instance().fetch(
                    client_id, max_bytes=METADATA_MAX_BYTES, accept=METADATA_ACCEPT
                )
            except UntrustedFetchError as exc:
                raise self._fetch_error(exc) from exc
            if not is_json_media_type(response.headers.get("content-type")):
                raise InvalidClientMetadata("content_type", "Response is not JSON")
            document = parse_json_object(response.content, InvalidClientMetadata)
            # Validate before caching: invalid documents are never stored
            validate_metadata(document, client_id)
            now = self._clock()
            fresh = freshness(response.headers, now, response_delay=max(0, now - requested_at))
            entry = _Entry(
                document=document,
                fetched_at=now,
                expires_at=now + fresh.ttl,
                stale_until=now + fresh.ttl + STALE_IF_ERROR,
            )
            self._store(key, entry)
            LOGGER.info(
                "CIMD metadata fetched",
                client_id=log_client_id(client_id),
                ttl=fresh.ttl,
                freshness=fresh.source,
                size=len(response.content),
                duration_ms=round((monotonic() - started) * 1000),
            )
            return entry
        except CIMDError as exc:
            outcome = exc.reason
            LOGGER.warning(
                "CIMD metadata fetch failed",
                client_id=log_client_id(client_id),
                reason=exc.reason,
                code=exc.code,
                duration_ms=round((monotonic() - started) * 1000),
            )
            raise
        finally:
            HIST_CIMD_FETCH.labels(outcome=outcome).observe(monotonic() - started)

    @staticmethod
    def _fetch_error(exc: UntrustedFetchError) -> CIMDError:
        if isinstance(exc, _TERMINAL_FETCH_ERRORS) or (
            isinstance(exc, UnexpectedStatus)
            and 400 <= exc.status < 500  # noqa: PLR2004
            and exc.status not in _TRANSIENT_STATUSES
        ):
            return MetadataRejected(f"fetch_{exc.reason}", "Document could not be fetched")
        return MetadataUnavailable(f"fetch_{exc.reason}", "Document could not be fetched")


_RESOLVER = PublicClientResolver()


def resolve_public_client(client_id: str, *, admit: Admit) -> CIMDClient:
    """Resolve `client_id` as a public CIMD client.

    `admit(client_id)` is the local admission check. It runs on every call,
    cache hits included, before anything is fetched; when it returns False,
    ClientNotAdmitted is raised. Raises a CIMDError subclass on any failure:
    check `.transient` to choose between a 503 and a terminal error, and use
    `.oauth_error` as the OAuth error code."""
    return _RESOLVER.resolve(client_id, admit=admit)


def invalidate(client_id: str) -> None:
    """Drop the cached metadata of `client_id` on all workers"""
    _RESOLVER.invalidate(client_id)
