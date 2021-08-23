"""Backend paths"""
BACKEND_DJANGO = "django.contrib.auth.backends.ModelBackend"
BACKEND_LDAP = "authentik.sources.ldap.auth.LDAPBackend"
BACKEND_APP_PASSWORD = "authentik.core.token_auth.TokenBackend"  # nosec
