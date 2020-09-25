"""OAuth Source Exception"""
from passbook.lib.sentry import SentryIgnoredException


class OAuthSourceException(SentryIgnoredException):
    """General Error during OAuth Flow occurred"""
