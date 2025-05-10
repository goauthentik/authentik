"""OAuth Source Exception"""

from authentik.common.exceptions import NotReportedException


class OAuthSourceException(NotReportedException):
    """General Error during OAuth Flow occurred"""
