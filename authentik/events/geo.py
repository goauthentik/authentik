"""events GeoIP Reader"""

from typing import Optional

from geoip2.database import Reader

from authentik.lib.config import CONFIG


def get_geoip_reader() -> Optional[Reader]:
    """Get GeoIP Reader, if configured, otherwise none"""
    path = CONFIG.y("authentik.geoip")
    if path == "":
        return None
    return Reader(path)


GEOIP_READER = get_geoip_reader()
