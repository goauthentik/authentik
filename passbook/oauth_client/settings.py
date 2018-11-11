"""
Oauth2 Client Settings
"""

AUTHENTICATION_BACKENDS = [
    'passbook.oauth_client.backends.AuthorizedServiceBackend',
]
