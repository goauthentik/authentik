"""OAuth Source Exception"""

from authentik.lib.otel import TracingIgnoredException


class OAuthSourceException(TracingIgnoredException):
    """General Error during OAuth Flow occurred"""
