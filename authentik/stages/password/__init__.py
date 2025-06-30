"""Backend paths"""

BACKEND_INBUILT = "authentik.core.auth.InbuiltBackend"
BACKEND_LDAP = "authentik.sources.ldap.auth.LDAPBackend"
BACKEND_APP_PASSWORD = "authentik.core.auth.TokenBackend"  # nosec
BACKEND_KERBEROS = "authentik.sources.kerberos.auth.KerberosBackend"
