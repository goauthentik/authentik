from authentik.lib.tracing import TracingIgnoredException


class GeoIPNotFoundException(TracingIgnoredException):
    """Exception raised when an IP is not found in a GeoIP database"""
