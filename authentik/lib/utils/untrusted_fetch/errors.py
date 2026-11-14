"""Errors raised by the untrusted URL fetcher.

Every error carries a short, fixed `reason` suitable for audit events and metric
labels. Messages never include response bodies."""


class UntrustedFetchError(Exception):
    """Base class for all fetch failures"""

    reason = "error"


class InvalidURL(UntrustedFetchError):
    """The URL is not acceptable for an untrusted fetch"""

    reason = "invalid_url"


class BlockedDestination(UntrustedFetchError):
    """The URL resolves to an address that may not be connected to"""

    reason = "blocked_destination"


class ResolutionError(UntrustedFetchError):
    """The hostname could not be resolved"""

    reason = "resolution_failed"


class ConnectError(UntrustedFetchError):
    """No connection could be established"""

    reason = "connect_failed"


class TLSError(UntrustedFetchError):
    """TLS handshake or certificate verification failed"""

    reason = "tls_failed"


class DeadlineExceeded(UntrustedFetchError):
    """The total deadline passed"""

    reason = "timeout"


class ConcurrencyLimitExceeded(UntrustedFetchError):
    """Too many fetches are in flight in this process"""

    reason = "concurrency_limit"


class ProtocolError(UntrustedFetchError):
    """The server sent a malformed response"""

    reason = "protocol_error"


class RedirectNotAllowed(UntrustedFetchError):
    """The server responded with a redirect, which is never followed"""

    reason = "redirect"

    def __init__(self, status: int):
        super().__init__(f"Redirects are not followed (HTTP {status})")
        self.status = status


class UnexpectedStatus(UntrustedFetchError):
    """The server responded with a non-200 status"""

    reason = "http_status"

    def __init__(self, status: int):
        super().__init__(f"Unexpected HTTP status {status}")
        self.status = status


class ResponseTooLarge(UntrustedFetchError):
    """The (decoded) response body exceeded the caller's limit"""

    reason = "too_large"


class UnsupportedContentEncoding(UntrustedFetchError):
    """The response used a content encoding that is not supported, or was corrupt"""

    reason = "content_encoding"
