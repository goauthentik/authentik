"""CIMD constants and limits.

Pinned to draft-ietf-oauth-client-id-metadata-document-03."""

CIMD_DRAFT = "draft-ietf-oauth-client-id-metadata-document-03"

# Response size limit. Draft -03 section 10.11 recommends reading at most 5 KB
# of metadata; the approved design allows 64 KiB to fit documents with inline JWKS.
METADATA_MAX_BYTES = 64 * 1024

# Structural JSON bounds
JSON_MAX_DEPTH = 8
JSON_MAX_ARRAY_ITEMS = 64
JSON_MAX_OBJECT_MEMBERS = 128

# Field-specific bounds
MAX_REDIRECT_URIS = 32
MAX_URI_LENGTH = 2048
MAX_CLIENT_NAME_LENGTH = 256
MAX_SHORT_STRING_LENGTH = 256
MAX_SCOPE_TOKENS = 64
MAX_GRANT_TYPES = 16
MAX_RESPONSE_TYPES = 16
MAX_JWKS_KEYS = 32
# Client IDs are truncated to this length in log events
LOG_CLIENT_ID_LENGTH = 128

# Cache freshness, in seconds. The minimum applies even to `no-store`/`no-cache`
# responses; `DEFAULT_TTL` is used when a response carries no cache policy.
MIN_TTL = 60
MAX_TTL = 300
DEFAULT_TTL = 120
# How long past its freshness a valid document may still be used, and only
# when refetching it fails transiently (draft -03 section 6.1)
STALE_IF_ERROR = 3600
# After a transient failure, a stale document is served without refetching for this long
STALE_RETRY_INTERVAL = 60

# OAuth values
AUTH_METHOD_NONE = "none"
# Shared-secret methods are prohibited by draft -03 section 4.1
SHARED_SECRET_AUTH_METHODS = frozenset(
    ("client_secret_basic", "client_secret_post", "client_secret_jwt")
)

GRANT_AUTHORIZATION_CODE = "authorization_code"
GRANT_REFRESH_TOKEN = "refresh_token"  # nosec
RESPONSE_TYPE_CODE = "code"

# The public profile: what a document may at most declare. Anything else it
# declares is dropped, so the document can only narrow these, never widen them.
PUBLIC_GRANT_TYPES = frozenset((GRANT_AUTHORIZATION_CODE, GRANT_REFRESH_TOKEN))
PUBLIC_RESPONSE_TYPES = frozenset((RESPONSE_TYPE_CODE,))

# RFC 7591 section 2 defaults, used when the document omits these fields
DEFAULT_GRANT_TYPES = (GRANT_AUTHORIZATION_CODE,)
DEFAULT_RESPONSE_TYPES = (RESPONSE_TYPE_CODE,)

# Loopback hosts whose plain-HTTP redirect URIs may use any port (RFC 8252
# section 7.3, decision O1). Compared with the host exactly as written.
LOOPBACK_REDIRECT_HOSTS = frozenset(("localhost", "127.0.0.1", "[::1]"))
