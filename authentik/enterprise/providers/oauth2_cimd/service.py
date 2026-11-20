"""Resolve a client ID URL into validated, cached metadata, capabilities and keys.

Cache design:

- Entries live in the shared Django cache (Postgres-backed in authentik), so
  every worker sees the same entries and invalidations.
- Each entry stores the parsed document, not the validated object. It is
  re-validated on every read, so validation changes apply to existing entries.
- Each entry carries its own wall-clock `expires_at`. An entry past it is never
  used; a failed refetch raises instead (fail closed). Failures are never cached.
- Each client has a generation token. `invalidate()` replaces it, which makes
  all of the client's metadata and JWKS entries unusable on every worker, even
  ones written by fetches that were in flight at the time.
- Concurrent fetches of one URL are coalesced: within a process through a
  shared in-flight call, across processes through an `add()` lock in the shared
  cache, which other workers wait on and then read the leader's entry.
"""

import secrets
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from time import monotonic, sleep, time
from typing import Any

from django.core.cache import BaseCache, cache, caches
from django.db import connection, connections, router, transaction
from django.utils.timezone import now as timezone_now
from django_postgres_cache.backend import DatabaseCache
from django_postgres_cache.models import CacheEntry
from structlog.stdlib import get_logger

from authentik.enterprise.providers.oauth2_cimd.bounded_json import (
    is_json_media_type,
    parse_json_object,
)
from authentik.enterprise.providers.oauth2_cimd.constants import (
    AUTH_METHOD_PRIVATE_KEY_JWT,
    JWKS_MAX_BYTES,
    KEY_REFRESH_INTERVAL,
    MAX_CACHE_ENTRIES,
    MAX_TTL,
    METADATA_MAX_BYTES,
)
from authentik.enterprise.providers.oauth2_cimd.errors import (
    CIMDError,
    ClientDisabled,
    InvalidClientKeys,
    InvalidClientMetadata,
    MetadataRejected,
    MetadataUnavailable,
    UnknownSigningKey,
)
from authentik.enterprise.providers.oauth2_cimd.freshness import freshness
from authentik.enterprise.providers.oauth2_cimd.jwks import ClientKey, ClientKeySet, validate_jwks
from authentik.enterprise.providers.oauth2_cimd.metadata import (
    ClientMetadata,
    validate_client_id,
    validate_metadata,
)
from authentik.enterprise.providers.oauth2_cimd.metrics import (
    COUNTER_CIMD_CACHE,
    COUNTER_CIMD_RESOLVE,
    HIST_CIMD_FETCH,
)
from authentik.enterprise.providers.oauth2_cimd.negotiation import (
    ClientProfile,
    EffectiveCapabilities,
    negotiate,
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

CACHE_PREFIX = "authentik_enterprise_oauth2_cimd"
ENTRY_VERSION = 2
METADATA_ACCEPT = "application/json"
JWKS_ACCEPT = "application/jwk-set+json, application/json"
# Lock lifetime on top of the fetcher's deadline, so a crashed leader can't block forever
LOCK_MARGIN = 2
POLL_INTERVAL = 0.1
# Generation tokens outlive every entry written before them
GENERATION_TIMEOUT = 2 * MAX_TTL + 60
# Fetch errors that retrying won't fix (draft -03 section 6.1 "terminal" errors)
_TERMINAL_FETCH_ERRORS = (
    InvalidURL,
    BlockedDestination,
    RedirectNotAllowed,
    ResponseTooLarge,
    UnsupportedContentEncoding,
)

# Called with the client ID. Returns False if the client is locally disabled or
# not admitted. Runs on every resolution, including cache hits.
LocalCheck = Callable[[str], bool]


class Kind(StrEnum):
    """Cached document kind"""

    METADATA = "metadata"
    JWKS = "jwks"


@dataclass(frozen=True)
class CachedMetadata:
    """Validated metadata and its freshness"""

    metadata: ClientMetadata
    fetched_at: float
    expires_at: float
    generation: str


@dataclass(frozen=True)
class CachedKeys:
    """Validated keys and their freshness. Inline keys share the metadata's freshness"""

    keys: ClientKeySet
    fetched_at: float
    expires_at: float
    generation: str


@dataclass(frozen=True)
class ResolvedClient:
    """A client ID resolved against a local profile"""

    client_id: str
    profile: ClientProfile
    metadata: ClientMetadata
    capabilities: EffectiveCapabilities
    # Validated signing keys; only loaded for profiles that use keys
    keys: ClientKeySet | None
    # Earliest expiry of the metadata and keys this was built from
    expires_at: float
    generation: str

    def is_fresh(self, now: float) -> bool:
        """True until the underlying metadata or keys expire"""
        return now < self.expires_at


class _Flight:
    """A fetch in progress in this process, shared by concurrent callers"""

    def __init__(self) -> None:
        self.done = threading.Event()
        self.result: dict[str, Any] | None = None
        self.error: CIMDError | None = None
        self.waiters = 0


def _hash(value: str) -> str:
    return sha256(value.encode()).hexdigest()


class ClientMetadataService:
    """Fetch, validate and cache client metadata documents and their keys.

    `local_check` is required so callers can't forget admission and disablement.
    It runs on every resolution, cache hit or not, before anything is fetched."""

    def __init__(
        self,
        *,
        local_check: LocalCheck,
        cache_backend: BaseCache | None = None,
        fetcher: UntrustedURLFetcher | None = None,
        clock: Callable[[], float] = time,
        sleep_func: Callable[[float], None] = sleep,
        max_entries: int = MAX_CACHE_ENTRIES,
        key_refresh_interval: int = KEY_REFRESH_INTERVAL,
    ):
        self.local_check = local_check
        self._cache = cache_backend if cache_backend is not None else cache
        self._fetcher = fetcher
        self._clock = clock
        self._sleep = sleep_func
        self.max_entries = max_entries
        self.key_refresh_interval = key_refresh_interval
        self._flights: dict[tuple[str, str, str | None], _Flight] = {}
        self._flights_lock = threading.Lock()

    # Public API

    def resolve(self, client_id: str, profile: ClientProfile) -> ResolvedClient:
        """Resolve `client_id` for `profile`.

        Raises a CIMDError subclass; never returns data past its freshness."""
        try:
            resolved = self._resolve(client_id, profile)
        except CIMDError as exc:
            COUNTER_CIMD_RESOLVE.labels(profile=profile.name, outcome=exc.reason).inc()
            LOGGER.info(
                "CIMD client rejected",
                client_id=client_id,
                profile=profile.name,
                reason=exc.reason,
                code=exc.code,
            )
            raise
        COUNTER_CIMD_RESOLVE.labels(profile=profile.name, outcome="success").inc()
        return resolved

    def find_signing_key(self, resolved: ResolvedClient, kid: str | None) -> ClientKey:
        """Find the key a client assertion names, for `private_key_jwt` verification.

        Re-resolves if `resolved` has expired. An unknown `kid` triggers at most
        one refresh per client per `key_refresh_interval`, across all workers.
        Without a `kid`, the client must have exactly one key."""
        self._check_local(resolved.client_id)
        if not resolved.is_fresh(self._clock()) or resolved.generation != self._generation(
            resolved.client_id
        ):
            resolved = self.resolve(resolved.client_id, resolved.profile)
        key = resolved.keys.find(kid) if resolved.keys else None
        if key is not None:
            self._check_snapshot(resolved.client_id, resolved.generation, resolved.expires_at)
            return key
        resolved = self.resolve(resolved.client_id, resolved.profile)
        key = resolved.keys.find(kid) if resolved.keys else None
        if key is not None:
            self._check_snapshot(resolved.client_id, resolved.generation, resolved.expires_at)
            return key
        if kid is None:
            raise UnknownSigningKey("ambiguous_key", "No kid and not exactly one key")
        refresh_key = f"{CACHE_PREFIX}:refresh:{_hash(resolved.client_id)}:{resolved.generation}"
        token = secrets.token_hex(8)
        started = self._clock()
        active = {"token": token, "active": True}
        if self._add(refresh_key, active, max(self.key_refresh_interval, self._lock_timeout())):
            try:
                LOGGER.info("CIMD unknown key ID, refreshing keys", client_id=resolved.client_id)
                refreshed = self._resolve(resolved.client_id, resolved.profile, refresh_keys=True)
            finally:
                if self._cache.get(refresh_key) == active:
                    remaining = max(0, self.key_refresh_interval - (self._clock() - started))
                    self._cache.set(refresh_key, {"token": token, "active": False}, remaining)
        else:
            deadline = monotonic() + self._lock_timeout()
            logical_deadline = self._clock() + self._lock_timeout()
            while (marker := self._cache.get(refresh_key)) and marker.get("active"):
                self._check_snapshot(resolved.client_id, resolved.generation, resolved.expires_at)
                if monotonic() >= deadline or self._clock() >= logical_deadline:
                    raise MetadataUnavailable("coalesce_timeout", "Timed out waiting for refresh")
                self._sleep(POLL_INTERVAL)
            refreshed = self.resolve(resolved.client_id, resolved.profile)
            key = refreshed.keys.find(kid) if refreshed.keys else None
            if key is None:
                raise UnknownSigningKey("refresh_rate_limited", "Unknown kid, refresh rate limited")
        key = refreshed.keys.find(kid) if refreshed.keys else None
        if key is None:
            raise UnknownSigningKey("unknown_kid", "No key with this kid")
        self._check_snapshot(refreshed.client_id, refreshed.generation, refreshed.expires_at)
        return key

    def get_metadata(self, client_id: str, *, force: bool = False) -> CachedMetadata:
        """Validated metadata for `client_id`, from cache or freshly fetched.

        Does not run the local check; use `resolve()` for request handling."""
        validate_client_id(client_id)
        entry_key = self._entry_key(Kind.METADATA, client_id)
        entry, generation = self._lookup(Kind.METADATA, client_id, entry_key)
        if entry is not None and not force:
            try:
                return self._metadata_from_entry(client_id, entry)
            except InvalidClientMetadata, InvalidClientKeys:
                # Validation became stricter since the entry was written
                self._cache.delete(entry_key)
        entry = self._load(
            Kind.METADATA,
            client_id,
            client_id,
            entry_key,
            generation,
            newer_than=entry["revision"] if entry is not None and force else None,
        )
        return self._metadata_from_entry(client_id, entry)

    def get_keys(self, cached: CachedMetadata, *, force: bool = False) -> CachedKeys | None:
        """Validated keys of a client: inline `jwks`, or fetched from `jwks_uri`.

        Returns None if the document declares no keys. `force` refetches `jwks_uri`."""
        metadata = cached.metadata
        self._check_snapshot(metadata.client_id, cached.generation, cached.expires_at)
        if metadata.jwks is not None:
            return CachedKeys(
                metadata.jwks, cached.fetched_at, cached.expires_at, cached.generation
            )
        if metadata.jwks_uri is None:
            return None
        entry_key = self._entry_key(Kind.JWKS, f"{metadata.client_id}\n{metadata.jwks_uri}")
        entry, generation = self._lookup(Kind.JWKS, metadata.client_id, entry_key)
        if generation != cached.generation:
            raise MetadataUnavailable("invalidated", "Client changed during resolution")
        if entry is not None and not force:
            try:
                return self._keys_from_entry(metadata.client_id, entry)
            except InvalidClientKeys:
                self._cache.delete(entry_key)
        entry = self._load(
            Kind.JWKS,
            metadata.client_id,
            metadata.jwks_uri,
            entry_key,
            generation,
            newer_than=entry["revision"] if entry is not None and force else None,
        )
        return self._keys_from_entry(metadata.client_id, entry)

    def invalidate(self, client_id: str) -> None:
        """Drop cached metadata and keys of `client_id` on all workers"""
        self._cache.set(
            self._generation_key(client_id), secrets.token_hex(8), timeout=GENERATION_TIMEOUT
        )
        self._cache.delete(self._entry_key(Kind.METADATA, client_id))
        LOGGER.info("CIMD client cache invalidated", client_id=client_id)

    # Resolution

    def _check_local(self, client_id: str) -> None:
        if not self.local_check(client_id):
            raise ClientDisabled("disabled", "Client is not admitted locally")

    def _generation(self, client_id: str) -> str:
        return self._cache.get(self._generation_key(client_id)) or "0"

    def _check_snapshot(self, client_id: str, generation: str, expires_at: float) -> None:
        if generation != self._generation(client_id):
            raise MetadataUnavailable("invalidated", "Client changed during resolution")
        if self._clock() >= expires_at:
            raise MetadataUnavailable("expired", "Client expired during resolution")

    def _resolve(
        self, client_id: str, profile: ClientProfile, *, refresh_keys: bool = False
    ) -> ResolvedClient:
        self._check_local(client_id)
        cached = self.get_metadata(client_id)
        if refresh_keys and cached.metadata.jwks is not None:
            # Inline keys rotate with the document itself
            cached = self.get_metadata(client_id, force=True)
        expires_at = cached.expires_at
        keys: ClientKeySet | None = None
        uses_keys = (
            profile.requires_signing_keys or AUTH_METHOD_PRIVATE_KEY_JWT in profile.auth_methods
        )
        # Public clients never need keys, so they're not fetched for them
        if uses_keys:
            cached_keys = self.get_keys(
                cached, force=refresh_keys and cached.metadata.jwks_uri is not None
            )
            if cached_keys is not None:
                keys = cached_keys.keys
                expires_at = min(expires_at, cached_keys.expires_at)
        capabilities = negotiate(cached.metadata, profile, keys)
        self._check_local(client_id)
        self._check_snapshot(client_id, cached.generation, expires_at)
        return ResolvedClient(
            client_id=client_id,
            profile=profile,
            metadata=cached.metadata,
            capabilities=capabilities,
            keys=keys,
            expires_at=expires_at,
            generation=cached.generation,
        )

    def _metadata_from_entry(self, client_id: str, entry: dict[str, Any]) -> CachedMetadata:
        metadata = validate_metadata(entry["document"], client_id)
        self._check_snapshot(client_id, entry["generation"], entry["expires_at"])
        return CachedMetadata(
            metadata=metadata,
            fetched_at=entry["fetched_at"],
            expires_at=entry["expires_at"],
            generation=entry["generation"],
        )

    def _keys_from_entry(self, client_id: str, entry: dict[str, Any]) -> CachedKeys:
        keys = validate_jwks(entry["document"])
        self._check_snapshot(client_id, entry["generation"], entry["expires_at"])
        return CachedKeys(
            keys=keys,
            fetched_at=entry["fetched_at"],
            expires_at=entry["expires_at"],
            generation=entry["generation"],
        )

    # Shared cache

    def _entry_key(self, kind: Kind, identity: str) -> str:
        return f"{CACHE_PREFIX}:{kind}:{_hash(identity)}"

    def _lock_key(self, entry_key: str) -> str:
        return f"{CACHE_PREFIX}:lock:{entry_key.removeprefix(CACHE_PREFIX + ':')}"

    def _generation_key(self, client_id: str) -> str:
        return f"{CACHE_PREFIX}:generation:{_hash(client_id)}"

    def _add(self, key: str, value: Any, timeout: float) -> bool:
        # Inside a transaction, a savepoint keeps a failed insert from aborting it
        if connection.in_atomic_block:
            with transaction.atomic():
                return self._cache.add(key, value, timeout=timeout)
        return self._cache.add(key, value, timeout=timeout)

    def _lookup(
        self, kind: Kind, client_id: str, entry_key: str, *, count: bool = True
    ) -> tuple[dict[str, Any] | None, str]:
        """Return the usable entry (or None) and the client's current generation"""
        generation_key = self._generation_key(client_id)
        values = self._cache.get_many([entry_key, generation_key])
        generation = values.get(generation_key) or "0"
        entry = values.get(entry_key)
        result = "hit"
        if not isinstance(entry, dict) or entry.get("version") != ENTRY_VERSION:
            result, entry = "miss", None
        elif entry.get("generation") != generation:
            result, entry = "invalidated", None
        elif entry.get("expires_at", 0) <= self._clock():
            result, entry = "expired", None
        if count:
            COUNTER_CIMD_CACHE.labels(kind=kind, result=result).inc()
        return entry, generation

    def _has_room(self, kind: Kind, entry_key: str) -> bool:
        counter = getattr(self._cache, "keys_count", None)
        if counter is None:
            return True
        if counter(f"{CACHE_PREFIX}:{kind}:*") < self.max_entries:
            return True
        # Replacing an existing entry doesn't grow the cache
        return self._cache.has_key(entry_key)

    def _store(self, kind: Kind, client_id: str, entry_key: str, entry: dict[str, Any]) -> None:
        self._check_snapshot(client_id, entry["generation"], entry["expires_at"])
        backend = caches["default"] if self._cache is cache else self._cache
        if isinstance(backend, DatabaseCache):
            alias = router.db_for_write(CacheEntry)
            prefix = backend.make_key(f"{CACHE_PREFIX}:{kind}:")
            lock_id = int.from_bytes(sha256(prefix.encode()).digest()[:8], signed=True)
            with transaction.atomic(using=alias):
                with connections[alias].cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
                entries = CacheEntry.objects.using(alias).filter(cache_key__startswith=prefix)
                entries.filter(expires__lt=timezone_now()).delete()
                if (
                    not entries.filter(cache_key=backend.make_key(entry_key)).exists()
                    and entries.count() >= self.max_entries
                ):
                    LOGGER.warning(
                        "CIMD cache is full, not caching", kind=kind, client_id=client_id
                    )
                    return
                self._check_snapshot(client_id, entry["generation"], entry["expires_at"])
                backend.set(entry_key, entry, timeout=int(entry["expires_at"] - self._clock()) + 1)
            return
        if not self._has_room(kind, entry_key):
            LOGGER.warning("CIMD cache is full, not caching", kind=kind, client_id=client_id)
            return
        ttl = entry["expires_at"] - self._clock()
        # Backend expiry has second granularity; `expires_at` stays authoritative
        self._cache.set(entry_key, entry, timeout=int(ttl) + 1)

    # Fetching and coalescing

    def _lock_timeout(self) -> float:
        return (self._fetcher or get_untrusted_fetcher()).timeout + LOCK_MARGIN

    def _load(
        self,
        kind: Kind,
        client_id: str,
        url: str,
        entry_key: str,
        generation: str,
        *,
        newer_than: str | None,
    ) -> dict[str, Any]:
        """Fetch and store a document, sharing one fetch between concurrent callers"""
        flight_key = (entry_key, generation, newer_than)
        with self._flights_lock:
            flight = self._flights.get(flight_key)
            leader = flight is None
            if flight is None:
                flight = self._flights[flight_key] = _Flight()
            else:
                flight.waiters += 1
        if not leader:
            if not flight.done.wait(self._lock_timeout()):
                raise MetadataUnavailable("coalesce_timeout", "Timed out waiting for fetch")
            if flight.error is not None:
                raise type(flight.error)(flight.error.code, str(flight.error))
            if flight.result is None:
                raise MetadataUnavailable("coalesced_fetch_failed", "Concurrent fetch failed")
            self._check_snapshot(client_id, generation, flight.result["expires_at"])
            return flight.result
        try:
            flight.result = self._load_shared(
                kind, client_id, url, entry_key, generation, newer_than=newer_than
            )
            self._check_snapshot(client_id, generation, flight.result["expires_at"])
            return flight.result
        except CIMDError as exc:
            flight.error = exc
            raise
        finally:
            with self._flights_lock:
                self._flights.pop(flight_key, None)
            flight.done.set()

    def _load_shared(
        self,
        kind: Kind,
        client_id: str,
        url: str,
        entry_key: str,
        generation: str,
        *,
        newer_than: str | None,
    ) -> dict[str, Any]:
        """Fetch under a cross-worker lock, or wait for the worker holding it"""
        lock_key = f"{self._lock_key(entry_key)}:{generation}"
        token = secrets.token_hex(8)
        lock_timeout = self._lock_timeout()
        if self._add(lock_key, token, lock_timeout):
            try:
                entry, current_generation = self._lookup(kind, client_id, entry_key, count=False)
                if current_generation != generation:
                    raise MetadataUnavailable("invalidated", "Client changed during resolution")
                if entry is not None and (newer_than is None or entry["revision"] != newer_than):
                    return entry
                return self._fetch(kind, client_id, url, entry_key, generation)
            finally:
                if self._cache.get(lock_key) == token:
                    self._cache.delete(lock_key)
        deadline = self._clock() + lock_timeout
        monotonic_deadline = monotonic() + lock_timeout
        while self._clock() < deadline and monotonic() < monotonic_deadline:
            self._sleep(POLL_INTERVAL)
            lock_released = self._cache.get(lock_key) is None
            entry, current_generation = self._lookup(kind, client_id, entry_key, count=False)
            if current_generation != generation:
                raise MetadataUnavailable("invalidated", "Client changed during resolution")
            if entry is not None and (newer_than is None or entry["revision"] != newer_than):
                return entry
            if lock_released:
                # The other worker failed. Failures aren't cached or shared, and
                # retrying here would multiply fetches against a failing host.
                raise MetadataUnavailable("coalesced_fetch_failed", "Concurrent fetch failed")
        raise MetadataUnavailable("coalesce_timeout", "Timed out waiting for fetch")

    def _fetch(
        self, kind: Kind, client_id: str, url: str, entry_key: str, generation: str
    ) -> dict[str, Any]:
        started = monotonic()
        requested_at = self._clock()
        fetcher = self._fetcher or get_untrusted_fetcher()
        outcome = "success"
        try:
            try:
                if kind == Kind.METADATA:
                    response = fetcher.fetch(
                        url, max_bytes=METADATA_MAX_BYTES, accept=METADATA_ACCEPT
                    )
                else:
                    response = fetcher.fetch(url, max_bytes=JWKS_MAX_BYTES, accept=JWKS_ACCEPT)
            except UntrustedFetchError as exc:
                raise self._fetch_error(exc) from exc
            error: type[CIMDError] = (
                InvalidClientMetadata if kind == Kind.METADATA else InvalidClientKeys
            )
            extra = () if kind == Kind.METADATA else ("application/jwk-set+json",)
            if not is_json_media_type(response.headers.get("content-type"), *extra):
                raise error("content_type", "Response is not JSON")
            document = parse_json_object(response.content, error)
            # Validate before caching: invalid documents are never stored
            if kind == Kind.METADATA:
                validate_metadata(document, client_id)
            else:
                validate_jwks(document)
            now = self._clock()
            fresh = freshness(response.headers, now, response_delay=max(0, now - requested_at))
            entry = {
                "version": ENTRY_VERSION,
                "generation": generation,
                "revision": secrets.token_hex(16),
                "document": document,
                "fetched_at": now,
                "expires_at": now + fresh.ttl,
            }
            self._store(kind, client_id, entry_key, entry)
            LOGGER.info(
                "CIMD document fetched",
                kind=kind,
                client_id=client_id,
                ttl=fresh.ttl,
                freshness=fresh.source,
                size=len(response.content),
                duration_ms=round((monotonic() - started) * 1000),
            )
            return entry
        except CIMDError as exc:
            outcome = exc.reason
            if isinstance(exc, InvalidClientMetadata | InvalidClientKeys):
                # A document that's now invalid must not stay usable
                self._cache.delete(entry_key)
            LOGGER.warning(
                "CIMD document fetch failed",
                kind=kind,
                client_id=client_id,
                reason=exc.reason,
                code=exc.code,
                duration_ms=round((monotonic() - started) * 1000),
            )
            raise
        finally:
            HIST_CIMD_FETCH.labels(kind=kind, outcome=outcome).observe(monotonic() - started)

    @staticmethod
    def _fetch_error(exc: UntrustedFetchError) -> CIMDError:
        if isinstance(exc, _TERMINAL_FETCH_ERRORS) or (
            isinstance(exc, UnexpectedStatus) and 400 <= exc.status < 500  # noqa: PLR2004
        ):
            return MetadataRejected(f"fetch_{exc.reason}", "Document could not be fetched")
        return MetadataUnavailable(f"fetch_{exc.reason}", "Document could not be fetched")
