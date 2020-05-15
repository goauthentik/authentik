"""passbook OAuth_Outlet"""
from django.conf import settings

CORS_ORIGIN_ALLOW_ALL = settings.DEBUG

REQUEST_APPROVAL_PROMPT = "auto"

INSTALLED_APPS = [
    "oauth2_provider",
    "corsheaders",
]
MIDDLEWARE = [
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]
AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend",
]

OAUTH2_PROVIDER_APPLICATION_MODEL = "passbook_channels_out_oauth.OAuth2Outlet"

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    "SCOPES": {
        "openid": "Access OpenID Userinfo",
        "openid:userinfo": "Access OpenID Userinfo",
        # 'write': 'Write scope',
        # 'groups': 'Access to your groups',
        "user:email": "GitHub Compatibility: User E-Mail",
        "read:org": "GitHub Compatibility: User Groups",
    }
}
