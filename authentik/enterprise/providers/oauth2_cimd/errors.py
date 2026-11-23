"""CIMD errors.

Every error has a fixed `reason` (a small set, safe as a metric label) and a
`code` (finer detail for audit logs). Messages never contain document contents.
`oauth_error` is the OAuth error the caller should return. `transient` errors
(draft -03 section 6.1) map to HTTP 503 at the token endpoint; all others are
terminal."""


class CIMDError(Exception):
    """Base class for all CIMD failures"""

    reason = "error"
    oauth_error = "invalid_client"
    transient = False

    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code)
        self.code = code


class InvalidClientID(CIMDError):
    """The client ID is not an acceptable client identifier URL"""

    reason = "invalid_client_id"


class ClientNotAdmitted(CIMDError):
    """The local admission check refused the client. Nothing was fetched"""

    reason = "not_admitted"


class InvalidClientMetadata(CIMDError):
    """The metadata document is malformed, inconsistent or prohibited"""

    reason = "invalid_metadata"


class UnsupportedClient(CIMDError):
    """The metadata is valid but doesn't describe a usable public client"""

    reason = "unsupported"


class MetadataUnavailable(CIMDError):
    """The document could not be fetched, for a reason that retrying may fix"""

    reason = "unavailable"
    oauth_error = "temporarily_unavailable"
    transient = True


class MetadataRejected(CIMDError):
    """The fetch failed in a way retrying won't fix (blocked, redirect, 4xx, too large)"""

    reason = "rejected"
