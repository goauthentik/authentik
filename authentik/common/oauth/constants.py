"""OAuth/OpenID Constants"""

from django.db import models
from django.utils.translation import gettext_lazy as _

GRANT_TYPE_AUTHORIZATION_CODE = "authorization_code"
GRANT_TYPE_IMPLICIT = "implicit"
GRANT_TYPE_REFRESH_TOKEN = "refresh_token"  # nosec
GRANT_TYPE_CLIENT_CREDENTIALS = "client_credentials"
GRANT_TYPE_PASSWORD = "password"  # nosec
GRANT_TYPE_DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"

QS_LOGIN_HINT = "login_hint"

CLIENT_ASSERTION = "client_assertion"
CLIENT_ASSERTION_TYPE = "client_assertion_type"
CLIENT_ASSERTION_TYPE_JWT = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"

PROMPT_NONE = "none"
PROMPT_CONSENT = "consent"
PROMPT_LOGIN = "login"

PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS = "goauthentik.io/providers/oauth2/iframe_sessions"

SCOPE_OPENID = "openid"
SCOPE_OPENID_PROFILE = "profile"
SCOPE_OPENID_EMAIL = "email"
SCOPE_OFFLINE_ACCESS = "offline_access"

UI_LOCALES = "ui_locales"

# https://www.iana.org/assignments/oauth-parameters/auth-parameters.xhtml#pkce-code-challenge-method
PKCE_METHOD_PLAIN = "plain"
PKCE_METHOD_S256 = "S256"

TOKEN_TYPE = "Bearer"  # nosec

SCOPE_AUTHENTIK_API = "goauthentik.io/api"

# URI schemes that are forbidden for redirect URIs
FORBIDDEN_URI_SCHEMES = {"javascript", "data", "vbscript"}

# Read/write full user (including email)
SCOPE_GITHUB_USER = "user"
# Read user (without email)
SCOPE_GITHUB_USER_READ = "read:user"
# Read users email addresses
SCOPE_GITHUB_USER_EMAIL = "user:email"
# Read info about teams
SCOPE_GITHUB_ORG_READ = "read:org"
SCOPE_GITHUB = {
    SCOPE_GITHUB_USER,
    SCOPE_GITHUB_USER_READ,
    SCOPE_GITHUB_USER_EMAIL,
    SCOPE_GITHUB_ORG_READ,
}

ACR_AUTHENTIK_DEFAULT = "goauthentik.io/providers/oauth2/default"

# https://datatracker.ietf.org/doc/html/draft-ietf-oauth-amr-values-06#section-2
AMR_PASSWORD = "pwd"  # nosec
AMR_MFA = "mfa"
AMR_OTP = "otp"
AMR_WEBAUTHN = "user"
AMR_SMART_CARD = "sc"


class SubModes(models.TextChoices):
    """Mode after which 'sub' attribute is generated, for compatibility reasons"""

    HASHED_USER_ID = "hashed_user_id", _("Based on the Hashed User ID")
    USER_ID = "user_id", _("Based on user ID")
    USER_UUID = "user_uuid", _("Based on user UUID")
    USER_USERNAME = "user_username", _("Based on the username")
    USER_EMAIL = (
        "user_email",
        _("Based on the User's Email. This is recommended over the UPN method."),
    )
    USER_UPN = (
        "user_upn",
        _(
            "Based on the User's UPN, only works if user has a 'upn' attribute set. "
            "Use this method only if you have different UPN and Mail domains."
        ),
    )
