"""CIMD constants and limits.

Pinned to draft-ietf-oauth-client-id-metadata-document-03."""

CIMD_DRAFT = "draft-ietf-oauth-client-id-metadata-document-03"

# Response size limits. Draft -03 section 10.11 recommends reading at most 5 KB
# of metadata; the approved design allows 64 KiB to fit documents with inline JWKS.
METADATA_MAX_BYTES = 64 * 1024
JWKS_MAX_BYTES = 128 * 1024

# Structural JSON bounds, applied to both metadata and JWKS documents
JSON_MAX_DEPTH = 8
JSON_MAX_ARRAY_ITEMS = 64
JSON_MAX_OBJECT_MEMBERS = 128

# Field-specific bounds
MAX_REDIRECT_URIS = 32
MAX_URI_LENGTH = 2048
MAX_CLIENT_NAME_LENGTH = 256
MAX_SHORT_STRING_LENGTH = 256
MAX_SCOPE_TOKENS = 64
MAX_AUTH_METHODS = 16
MAX_GRANT_TYPES = 16
MAX_RESPONSE_TYPES = 16
MAX_JWKS_KEYS = 32

# Cache freshness, in seconds. The minimum applies even to `no-store`/`no-cache`
# responses; `DEFAULT_TTL` is used when a response carries no cache policy.
MIN_TTL = 60
MAX_TTL = 300
DEFAULT_TTL = 120
# Upper bound on cached documents per kind (metadata, JWKS). Together with the
# size limits above this bounds the bytes held in the shared cache.
MAX_CACHE_ENTRIES = 1000
# Unknown-`kid` refreshes per client are limited to one per interval, across workers
KEY_REFRESH_INTERVAL = 30

# OAuth values
AUTH_METHOD_NONE = "none"
AUTH_METHOD_PRIVATE_KEY_JWT = "private_key_jwt"  # nosec
# Shared-secret methods are prohibited by draft -03 section 4.1
SHARED_SECRET_AUTH_METHODS = frozenset(
    ("client_secret_basic", "client_secret_post", "client_secret_jwt")
)

GRANT_AUTHORIZATION_CODE = "authorization_code"
GRANT_REFRESH_TOKEN = "refresh_token"  # nosec
GRANT_CLIENT_CREDENTIALS = "client_credentials"
GRANT_DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"
GRANT_TOKEN_EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"  # nosec
GRANT_JWT_BEARER = "urn:ietf:params:oauth:grant-type:jwt-bearer"
RESPONSE_TYPE_CODE = "code"

# RFC 7591 section 2 defaults, used when the document omits these fields
DEFAULT_GRANT_TYPES = (GRANT_AUTHORIZATION_CODE,)
DEFAULT_RESPONSE_TYPES = (RESPONSE_TYPE_CODE,)

PKCE_METHOD_S256 = "S256"

# Asymmetric JWS algorithms accepted for client keys
SIGNING_ALGS_BY_KTY = {
    "RSA": frozenset(("RS256", "RS384", "RS512", "PS256", "PS384", "PS512")),
    "EC": frozenset(("ES256", "ES384", "ES512")),
    "OKP": frozenset(("EdDSA",)),
}
SIGNING_ALGS = frozenset().union(*SIGNING_ALGS_BY_KTY.values())
EC_ALG_CURVES = {"ES256": "P-256", "ES384": "P-384", "ES512": "P-521"}
OKP_CURVES = frozenset(("Ed25519", "Ed448"))
RSA_MIN_KEY_SIZE = 2048
RSA_MAX_KEY_SIZE = 8192
