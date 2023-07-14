"""OAuth/OpenID Constants"""

GRANT_TYPE_AUTHORIZATION_CODE = "authorization_code"
GRANT_TYPE_IMPLICIT = "implicit"
GRANT_TYPE_REFRESH_TOKEN = "refresh_token"  # nosec
GRANT_TYPE_CLIENT_CREDENTIALS = "client_credentials"
GRANT_TYPE_PASSWORD = "password"  # nosec
GRANT_TYPE_DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"

CLIENT_ASSERTION_TYPE = "client_assertion_type"
CLIENT_ASSERTION = "client_assertion"
CLIENT_ASSERTION_TYPE_JWT = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"

PROMPT_NONE = "none"
PROMPT_CONSENT = "consent"
PROMPT_LOGIN = "login"

SCOPE_OPENID = "openid"
SCOPE_OPENID_PROFILE = "profile"
SCOPE_OPENID_EMAIL = "email"

# https://www.iana.org/assignments/oauth-parameters/\
#   oauth-parameters.xhtml#pkce-code-challenge-method
PKCE_METHOD_PLAIN = "plain"
PKCE_METHOD_S256 = "S256"

TOKEN_TYPE = "Bearer"  # nosec

SCOPE_AUTHENTIK_API = "goauthentik.io/api"

# Read/write full user (including email)
SCOPE_GITHUB_USER = "user"
# Read user (without email)
SCOPE_GITHUB_USER_READ = "read:user"
# Read users email addresses
SCOPE_GITHUB_USER_EMAIL = "user:email"
# Read info about teams
SCOPE_GITHUB_ORG_READ = "read:org"

ACR_AUTHENTIK_DEFAULT = "goauthentik.io/providers/oauth2/default"

# https://datatracker.ietf.org/doc/html/draft-ietf-oauth-amr-values-06#section-2
AMR_PASSWORD = "pwd"  # nosec
AMR_MFA = "mfa"
AMR_OTP = "otp"
AMR_WEBAUTHN = "user"
