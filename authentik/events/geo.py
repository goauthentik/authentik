"""events GeoIP Reader"""
from typing import Optional

from geoip2.database import Reader
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()


def get_geoip_reader() -> Optional[Reader]:
    """Get GeoIP Reader, if configured, otherwise none"""
    path = CONFIG.y("authentik.geoip")
    if path == "" or not path:
        return None
    try:
        reader = Reader(path)
        LOGGER.info("Enabled GeoIP support")
        return reader
    except OSError:
        return None


GEOIP_READER = get_geoip_reader()
