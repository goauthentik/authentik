"""events GeoIP Reader"""
from datetime import datetime
from os import stat
from time import time
from typing import Optional, TypedDict

from geoip2.database import Reader
from geoip2.errors import GeoIP2Error
from geoip2.models import City
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG

LOGGER = get_logger()


class GeoIPDict(TypedDict):
    """GeoIP Details"""

    continent: str
    country: str
    lat: float
    long: float
    city: str


class GeoIPReader:
    """Slim wrapper around GeoIP API"""

    __reader: Optional[Reader] = None
    __last_mtime: float = 0.0

    def __init__(self):
        self.__open()

    def __open(self):
        """Get GeoIP Reader, if configured, otherwise none"""
        path = CONFIG.y("authentik.geoip")
        if path == "" or not path:
            return
        try:
            reader = Reader(path)
            LOGGER.info("Loaded GeoIP database")
            self.__reader = reader
            self.__last_mtime = stat(path).st_mtime
        except OSError as exc:
            LOGGER.warning("Failed to load GeoIP database", exc=exc)

    def __check_expired(self):
        """Check if the geoip database has been opened longer than 8 hours,
        and re-open it, as it will probably will have been re-downloaded"""
        now = time()
        diff = datetime.fromtimestamp(now) - datetime.fromtimestamp(self.__last_mtime)
        diff_hours = diff.total_seconds() // 3600
        if diff_hours >= 8:
            LOGGER.info("GeoIP databased loaded too long, re-opening", diff=diff)
            self.__open()

    @property
    def enabled(self) -> bool:
        """Check if GeoIP is enabled"""
        return bool(self.__reader)

    def city(self, ip_address: str) -> Optional[City]:
        """Wrapper for Reader.city"""
        if not self.enabled:
            return None
        self.__check_expired()
        try:
            return self.__reader.city(ip_address)
        except (GeoIP2Error, ValueError):
            return None

    def city_dict(self, ip_address: str) -> Optional[GeoIPDict]:
        """Wrapper for self.city that returns a dict"""
        city = self.city(ip_address)
        if not city:
            return None
        city_dict: GeoIPDict = {
            "continent": city.continent.code,
            "country": city.country.iso_code,
            "lat": city.location.latitude,
            "long": city.location.longitude,
            "city": "",
        }
        if city.city.name:
            city_dict["city"] = city.city.name
        return city_dict


GEOIP_READER = GeoIPReader()
