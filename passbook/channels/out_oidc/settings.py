"""passbook OIDC Provider"""

INSTALLED_APPS = [
    "oidc_provider",
]

OIDC_AFTER_USERLOGIN_HOOK = "passbook.channels.out_oidc.auth.check_permissions"
OIDC_IDTOKEN_INCLUDE_CLAIMS = True
OIDC_USERINFO = "passbook.channels.out_oidc.claims.userinfo"
