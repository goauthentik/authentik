"""Oauth2 Client Settings"""

AUTHENTICATION_BACKENDS = [
    "passbook.channels.in_oauth.backends.AuthorizedServiceBackend",
]

PASSBOOK_SOURCES_OAUTH_TYPES = [
    "passbook.channels.in_oauth.types.discord",
    "passbook.channels.in_oauth.types.facebook",
    "passbook.channels.in_oauth.types.github",
    "passbook.channels.in_oauth.types.google",
    "passbook.channels.in_oauth.types.reddit",
    "passbook.channels.in_oauth.types.twitter",
    "passbook.channels.in_oauth.types.azure_ad",
]
