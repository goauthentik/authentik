from authentik.common.exceptions import NotReportedException


class GeoIPNotFoundException(NotReportedException):
    """Exception raised when an IP is not found in a GeoIP database"""
