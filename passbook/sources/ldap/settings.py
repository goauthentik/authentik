"""LDAP Settings"""

AUTHENTICATION_BACKENDS = [
    'passbook.sources.ldap.auth.LDAPBackend',
]
