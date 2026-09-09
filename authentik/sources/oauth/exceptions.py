"""OAuth Source Exception"""

from authentik.lib.tracing.exceptions import TracingIgnoredException


class OAuthSourceException(TracingIgnoredException):
    """General Error during OAuth Flow occurred"""
