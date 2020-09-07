"""OAuth/OpenID Constants"""

GRANT_TYPE_AUTHORIZATION_CODE = "authorization_code"
GRANT_TYPE_REFRESH_TOKEN = "refresh_token"
PROMPT_NONE = "none"
PROMPT_CONSNET = "consent"
SCOPE_OPENID = "openid"
SCOPE_OPENID_PROFILE = "profile"
SCOPE_OPENID_EMAIL = "email"
SCOPE_OPENID_INTROSPECTION = "token_introspection"

# Read/write full user (including email)
SCOPE_GITHUB_USER = "user"
# Read user (without email)
SCOPE_GITHUB_USER_READ = "read:user"
# Read users email addresses
SCOPE_GITHUB_USER_EMAIL = "user:email"
# Read info about teams
SCOPE_GITHUB_ORG_READ = "read:org"
