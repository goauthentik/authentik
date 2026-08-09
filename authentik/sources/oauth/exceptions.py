"""OAuth Source Exception"""

from authentik.lib.sentry import SentryIgnoredException


class OAuthSourceException(SentryIgnoredException):
    """General Error during OAuth Flow occurred"""
