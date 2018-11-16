"""LDAP Settings"""

AUTHENTICATION_BACKENDS = [
    'passbook.ldap.auth.LDAPBackend',
]
