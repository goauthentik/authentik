from authentik.lib.sentry import SentryIgnoredException


class GeoIPNotFoundException(SentryIgnoredException):
    """Exception raised when an IP is not found in a GeoIP database"""
