"""Oauth2 Client Settings"""

AUTHENTICATION_BACKENDS = [
    "passbook.sources.oauth.backends.AuthorizedServiceBackend",
]

PASSBOOK_SOURCES_OAUTH_TYPES = [
    "passbook.sources.oauth.types.discord",
    "passbook.sources.oauth.types.facebook",
    "passbook.sources.oauth.types.github",
    "passbook.sources.oauth.types.google",
    "passbook.sources.oauth.types.reddit",
    "passbook.sources.oauth.types.twitter",
    "passbook.sources.oauth.types.azure_ad",
]
