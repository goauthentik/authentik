"""CIMD errors.

Every error has a fixed `reason` (a small set, safe as a metric label) and a
fixed `code` (finer detail for audit logs). Messages never contain document
contents. `oauth_error` is the OAuth error the caller should return."""


class CIMDError(Exception):
    """Base class for all CIMD failures"""

    reason = "error"
    oauth_error = "invalid_client"
    # Transient failures map to HTTP 503 at the token/PAR endpoints (draft -03 section 6.1)
    transient = False

    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code)
        self.code = code


class InvalidClientID(CIMDError):
    """The client ID is not an acceptable client identifier URL"""

    reason = "invalid_client_id"


class InvalidClientMetadata(CIMDError):
    """The metadata document is malformed, inconsistent or prohibited"""

    reason = "invalid_metadata"


class InvalidClientKeys(CIMDError):
    """The JWKS is malformed or contains private or symmetric key material"""

    reason = "invalid_jwks"


class UnsupportedClient(CIMDError):
    """The metadata is valid but no usable configuration exists for the required profile"""

    reason = "unsupported"


class MetadataUnavailable(CIMDError):
    """The document could not be fetched. Never served from an expired cache entry"""

    reason = "unavailable"
    oauth_error = "temporarily_unavailable"
    transient = True


class MetadataRejected(CIMDError):
    """The fetch failed in a way retrying won't fix (blocked, redirect, 4xx, too large)"""

    reason = "rejected"


class ClientDisabled(CIMDError):
    """The local check (admission, disablement) rejected the client"""

    reason = "disabled"


class UnknownSigningKey(CIMDError):
    """No usable signing key matches the presented key ID"""

    reason = "unknown_key"
