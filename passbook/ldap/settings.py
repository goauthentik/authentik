"""
LDAP Settings
"""

AUTHENTICATION_BACKENDS = [
    'supervisr.mod.auth.ldap.auth.LDAPBackend',
]
