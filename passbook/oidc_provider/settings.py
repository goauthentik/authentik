"""passbook OIDC Provider"""

INSTALLED_APPS = [
    'oidc_provider',
]

OIDC_AFTER_USERLOGIN_HOOK = "passbook.oidc_provider.lib.check_permissions"
