"""Hardened fetcher for untrusted URLs"""

import re
import threading
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from ipaddress import IPv6Address, ip_address
from time import monotonic
from urllib.parse import urlsplit

from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.utils.http import authentik_user_agent
from authentik.lib.utils.untrusted_fetch.errors import (
    BlockedDestination,
    ConcurrencyLimitExceeded,
    ConnectError,
    InvalidURL,
    ProtocolError,
    RedirectNotAllowed,
    ResponseTooLarge,
    UnexpectedStatus,
    UnsupportedContentEncoding,
)
from authentik.lib.utils.untrusted_fetch.policy import DestinationPolicy, IPAddress
from authentik.lib.utils.untrusted_fetch.transport import (
    ConnectTarget,
    Deadline,
    HTTPClientTransport,
    Resolver,
    SystemResolver,
    Transport,
    TransportResponse,
)

LOGGER = get_logger()

DEFAULT_TIMEOUT = 5.0
MIN_TIMEOUT = 0.5
MAX_TIMEOUT = 30.0
DEFAULT_MAX_CONCURRENCY = 10
MAX_CONCURRENCY = 64
DEFAULT_MAX_URL_LENGTH = 2048
# Hard ceiling on caller-supplied body limits, so a caller can't accidentally
# turn this into an unbounded download.
MAX_BYTES_CEILING = 1024 * 1024
# Allowance for gzip framing on top of the decoded limit when bounding raw bytes
_ENCODED_OVERHEAD = 1024
_READ_CHUNK = 16 * 1024

_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
# Percent-encoded '.', '/', '\' and NUL make path normalization ambiguous
_UNSAFE_ESCAPE_RE = re.compile(r"%(?:2e|2f|5c|00)", re.IGNORECASE)
_BAD_ESCAPE_RE = re.compile(r"%(?![0-9a-fA-F]{2})")
_GZIP_ENCODINGS = frozenset(("gzip", "x-gzip"))
_REDIRECT_STATUSES = frozenset((301, 302, 303, 307, 308))


@dataclass(frozen=True)
class UntrustedURL:
    """A validated URL, split into what's needed to connect"""

    url: str
    hostname: str
    port: int
    path: str
    ip_literal: IPAddress | None

    @property
    def host_header(self) -> str:
        """Value for the Host header"""
        host = f"[{self.hostname}]" if isinstance(self.ip_literal, IPv6Address) else self.hostname
        return host if self.port == 443 else f"{host}:{self.port}"  # noqa: PLR2004


@dataclass(frozen=True)
class FetchResponse:
    """A successful (HTTP 200) response"""

    url: str
    status: int
    headers: dict[str, str]
    content: bytes
    address: str


def _valid_dns_name(hostname: str) -> bool:
    if len(hostname) > 253:  # noqa: PLR2004
        return False
    labels = hostname.split(".")
    if not all(_LABEL_RE.match(label) for label in labels):
        return False
    # An all-numeric last label is never a valid hostname, and resolvers may
    # interpret forms like "127.1" or "2130706433" as IPv4 addresses.
    return not labels[-1].isdigit()


def parse_untrusted_url(url: str, max_length: int = DEFAULT_MAX_URL_LENGTH) -> UntrustedURL:
    """Validate an untrusted URL. Raises InvalidURL"""
    if not isinstance(url, str) or not url:
        raise InvalidURL("URL must be a non-empty string")
    if len(url) > max_length:
        raise InvalidURL("URL is too long")
    if not url.isascii() or any(c <= " " or c == "\x7f" for c in url) or "\\" in url:
        raise InvalidURL("URL contains disallowed characters")
    if "?" in url:
        raise InvalidURL("URL must not contain a query")
    if "#" in url:
        raise InvalidURL("URL must not contain a fragment")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise InvalidURL("Malformed URL") from exc
    if parts.scheme != "https" or not url.startswith("https://"):
        raise InvalidURL("URL must use https")
    if "@" in parts.netloc or parts.username is not None or parts.password is not None:
        raise InvalidURL("URL must not contain credentials")
    hostname = (parts.hostname or "").rstrip(".")
    if not hostname:
        raise InvalidURL("URL must contain a host")
    if "%" in hostname:
        raise InvalidURL("URL must not contain an IPv6 zone")
    if port is None:
        port = 443
    if port == 0:
        raise InvalidURL("Invalid port")
    ip_literal: IPAddress | None = None
    try:
        ip_literal = ip_address(hostname)
    except ValueError:
        if parts.netloc.startswith("["):
            raise InvalidURL("Invalid IPv6 literal") from None
        if not _valid_dns_name(hostname):
            raise InvalidURL("Invalid hostname") from None
    path = parts.path or "/"
    if not path.startswith("/"):
        raise InvalidURL("Invalid path")
    if any(segment in (".", "..") for segment in path.split("/")):
        raise InvalidURL("URL path must not contain dot segments")
    if _UNSAFE_ESCAPE_RE.search(path) or _BAD_ESCAPE_RE.search(path):
        raise InvalidURL("URL path contains unsafe escapes")
    return UntrustedURL(url=url, hostname=hostname, port=port, path=path, ip_literal=ip_literal)


def _content_encoding(headers: dict[str, str]) -> str | None:
    tokens = [
        token.strip().lower()
        for token in headers.get("content-encoding", "").split(",")
        if token.strip()
    ]
    tokens = [token for token in tokens if token != "identity"]  # nosec B105
    if not tokens:
        return None
    if len(tokens) == 1 and tokens[0] in _GZIP_ENCODINGS:
        return "gzip"
    raise UnsupportedContentEncoding("Unsupported content encoding")


def _read_body(
    response: TransportResponse,
    headers: dict[str, str],
    max_bytes: int,
    deadline: Deadline,
) -> bytes:
    encoding = _content_encoding(headers)
    raw_limit = max_bytes if encoding is None else max_bytes + _ENCODED_OVERHEAD
    if "content-length" in headers:
        try:
            declared = int(headers["content-length"])
        except ValueError:
            raise ProtocolError("Invalid Content-Length") from None
        if declared < 0:
            raise ProtocolError("Invalid Content-Length")
        if declared > raw_limit:
            raise ResponseTooLarge("Declared Content-Length exceeds limit")
    decoder = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS) if encoding else None
    body = bytearray()
    raw_read = 0
    while True:
        chunk = response.read_chunk(min(_READ_CHUNK, raw_limit - raw_read + 1), deadline)
        deadline.remaining()
        if not chunk:
            break
        raw_read += len(chunk)
        if raw_read > raw_limit:
            raise ResponseTooLarge("Response body exceeds limit")
        if decoder is None:
            body += chunk
        else:
            if decoder.eof:
                raise UnsupportedContentEncoding("Trailing data after gzip stream")
            try:
                body += decoder.decompress(chunk, max_bytes - len(body) + 1)
            except zlib.error as exc:
                raise UnsupportedContentEncoding("Corrupt gzip stream") from exc
            if decoder.unused_data:
                raise UnsupportedContentEncoding("Trailing data after gzip stream")
        if len(body) > max_bytes:
            raise ResponseTooLarge("Decoded response body exceeds limit")
    if decoder is not None and not decoder.eof:
        raise UnsupportedContentEncoding("Truncated gzip stream")
    return bytes(body)


def _collect_headers(raw: list[tuple[str, str]]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for name, value in raw:
        key = name.lower()
        headers[key] = f"{headers[key]}, {value}" if key in headers else value
    return headers


class UntrustedURLFetcher:
    """Fetch untrusted URLs (for example OAuth client metadata documents or JWKS).

    - HTTPS only, with certificate and hostname verification
    - no credentials, queries, fragments, or dot segments in URLs
    - redirects are never followed, proxies are never used
    - every resolved address is checked against a `DestinationPolicy` and the
      connection goes to the checked address (no second DNS lookup)
    - total deadline, decoded-size limit, and a per-process concurrency limit
    - requests only carry Host, User-Agent, Accept, Accept-Encoding and
      Connection headers; never cookies, credentials or caller headers
    """

    def __init__(
        self,
        *,
        policy: DestinationPolicy | None = None,
        resolver: Resolver | None = None,
        transport: Transport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        max_url_length: int = DEFAULT_MAX_URL_LENGTH,
        clock: Callable[[], float] = monotonic,
    ):
        self.policy = policy or DestinationPolicy()
        self.timeout = min(max(float(timeout), MIN_TIMEOUT), MAX_TIMEOUT)
        self.max_concurrency = min(max(int(max_concurrency), 1), MAX_CONCURRENCY)
        self.max_url_length = max_url_length
        self.resolver = resolver or SystemResolver(max_workers=self.max_concurrency)
        self.transport = transport or HTTPClientTransport()
        self._clock = clock
        self._slots = threading.BoundedSemaphore(self.max_concurrency)
        self._user_agent = authentik_user_agent()

    @classmethod
    def from_config(cls, **kwargs) -> UntrustedURLFetcher:
        """Create a fetcher configured from `untrusted_fetch.*` settings"""
        try:
            timeout = float(CONFIG.get("untrusted_fetch.timeout", DEFAULT_TIMEOUT))
        except TypeError, ValueError:
            timeout = DEFAULT_TIMEOUT
        kwargs.setdefault("timeout", timeout)
        kwargs.setdefault(
            "max_concurrency",
            CONFIG.get_int("untrusted_fetch.max_concurrency", DEFAULT_MAX_CONCURRENCY),
        )
        kwargs.setdefault(
            "policy",
            DestinationPolicy.from_config_value(
                CONFIG.get("untrusted_fetch.allowed_private_destinations", [])
            ),
        )
        return cls(**kwargs)

    def _resolve(self, target: UntrustedURL, deadline: Deadline) -> list[IPAddress]:
        if target.ip_literal is not None:
            addresses = [target.ip_literal]
            hostname = None
        else:
            addresses = self.resolver.resolve(target.hostname, target.port, deadline)
            hostname = target.hostname
        # Every address must pass: a partially poisoned answer is rejected outright
        for address in addresses:
            decision = self.policy.check(address, hostname)
            if not decision.allowed:
                LOGGER.info(
                    "Blocked untrusted fetch destination",
                    host=target.hostname,
                    reason=decision.reason,
                )
                raise BlockedDestination(f"Destination not allowed ({decision.reason})")
        return addresses

    def _headers(self, target: UntrustedURL, accept: str) -> tuple[tuple[str, str], ...]:
        return (
            ("Host", target.host_header),
            ("User-Agent", self._user_agent),
            ("Accept", accept),
            ("Accept-Encoding", "gzip"),
            ("Connection", "close"),
        )

    def fetch(
        self,
        url: str,
        *,
        max_bytes: int,
        accept: str = "application/json",
    ) -> FetchResponse:
        """Fetch `url` with GET and return its body, at most `max_bytes` decoded bytes.

        Raises a subclass of `UntrustedFetchError` on any failure, including any
        status other than 200."""
        if not 0 < max_bytes <= MAX_BYTES_CEILING:
            raise ValueError(f"max_bytes must be between 1 and {MAX_BYTES_CEILING}")
        if not accept.isascii() or any(c in accept for c in "\r\n\0"):
            raise ValueError("Invalid accept value")
        target = parse_untrusted_url(url, self.max_url_length)
        deadline = Deadline(self.timeout, self._clock)
        if not self._slots.acquire(timeout=deadline.remaining()):
            raise ConcurrencyLimitExceeded("Too many concurrent fetches")
        try:
            return self._fetch(target, max_bytes, accept, deadline)
        finally:
            self._slots.release()

    def _fetch(
        self,
        target: UntrustedURL,
        max_bytes: int,
        accept: str,
        deadline: Deadline,
    ) -> FetchResponse:
        addresses = self._resolve(target, deadline)
        headers = self._headers(target, accept)
        last_error: ConnectError | None = None
        for address in addresses:
            connect = ConnectTarget(
                address=address,
                hostname=target.hostname,
                port=target.port,
                path=target.path,
                headers=headers,
            )
            try:
                response = self.transport.open(connect, deadline)
            except ConnectError as exc:
                last_error = exc
                continue
            try:
                response_headers = _collect_headers(response.headers)
                if response.status in _REDIRECT_STATUSES:
                    raise RedirectNotAllowed(response.status)
                if response.status != 200:  # noqa: PLR2004
                    raise UnexpectedStatus(response.status)
                content = _read_body(response, response_headers, max_bytes, deadline)
            finally:
                response.close()
            return FetchResponse(
                url=target.url,
                status=response.status,
                headers=response_headers,
                content=content,
                address=str(address),
            )
        raise last_error or ConnectError("No address could be connected to")


_fetcher: UntrustedURLFetcher | None = None
_fetcher_override: UntrustedURLFetcher | None = None
_fetcher_lock = threading.Lock()


def get_untrusted_fetcher() -> UntrustedURLFetcher:
    """Process-wide fetcher configured from settings.

    Tests can substitute it with `authentik.lib.utils.untrusted_fetch.testing.use_fetcher`."""
    global _fetcher  # noqa: PLW0603
    if _fetcher_override is not None:
        return _fetcher_override
    with _fetcher_lock:
        if _fetcher is None:
            _fetcher = UntrustedURLFetcher.from_config()
        return _fetcher
