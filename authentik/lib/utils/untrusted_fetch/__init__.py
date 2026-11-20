"""Hardened HTTP fetcher for untrusted URLs (OAuth client metadata, JWKS, ...).

Use `get_untrusted_fetcher().fetch(url, max_bytes=...)`. Never use the generic
`get_http_session()` for URLs supplied by clients or remote documents."""

from authentik.lib.utils.untrusted_fetch.errors import (
    BlockedDestination,
    ConcurrencyLimitExceeded,
    ConnectError,
    DeadlineExceeded,
    InvalidURL,
    ProtocolError,
    RedirectNotAllowed,
    ResolutionError,
    ResponseTooLarge,
    TLSError,
    UnexpectedStatus,
    UnsupportedContentEncoding,
    UntrustedFetchError,
)
from authentik.lib.utils.untrusted_fetch.fetcher import (
    FetchResponse,
    UntrustedURL,
    UntrustedURLFetcher,
    get_untrusted_fetcher,
    parse_untrusted_url,
)
from authentik.lib.utils.untrusted_fetch.policy import (
    ALWAYS_BLOCKED_NETWORKS,
    AddressDecision,
    DestinationPolicy,
)

__all__ = [
    "ALWAYS_BLOCKED_NETWORKS",
    "AddressDecision",
    "BlockedDestination",
    "ConcurrencyLimitExceeded",
    "ConnectError",
    "DeadlineExceeded",
    "DestinationPolicy",
    "FetchResponse",
    "InvalidURL",
    "ProtocolError",
    "RedirectNotAllowed",
    "ResolutionError",
    "ResponseTooLarge",
    "TLSError",
    "UnexpectedStatus",
    "UnsupportedContentEncoding",
    "UntrustedFetchError",
    "UntrustedURL",
    "UntrustedURLFetcher",
    "get_untrusted_fetcher",
    "parse_untrusted_url",
]
