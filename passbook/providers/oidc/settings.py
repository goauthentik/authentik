"""passbook OIDC Provider"""

INSTALLED_APPS = [
    'oidc_provider',
]

OIDC_AFTER_USERLOGIN_HOOK = "passbook.providers.oidc.lib.check_permissions"
