"""events GeoIP Reader"""

from typing import Optional

from geoip2.database import Reader

from authentik.lib.config import CONFIG


def get_geoip_reader() -> Optional[Reader]:
    """Get GeoIP Reader, if configured, otherwise none"""
    path = CONFIG.y("authentik.geoip")
    if path == "" or not path:
        return None
    try:
        return Reader(path)
    except OSError:
        return None


GEOIP_READER = get_geoip_reader()
