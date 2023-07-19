"""events GeoIP Reader"""
from os import stat
from typing import Optional, TypedDict

from geoip2.database import Reader
from geoip2.errors import GeoIP2Error
from geoip2.models import City
from sentry_sdk.hub import Hub
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

    def __init__(self):
        self.__reader: Optional[Reader] = None
        self.__last_mtime: float = 0.0
        self.__open()

    def __open(self):
        """Get GeoIP Reader, if configured, otherwise none"""
        path = CONFIG.get("geoip")
        if path == "" or not path:
            return
        try:
            self.__reader = Reader(path)
            self.__last_mtime = stat(path).st_mtime
            LOGGER.info("Loaded GeoIP database", last_write=self.__last_mtime)
        except OSError as exc:
            LOGGER.warning("Failed to load GeoIP database", exc=exc)

    def __check_expired(self):
        """Check if the modification date of the GeoIP database has
        changed, and reload it if so"""
        path = CONFIG.get("geoip")
        try:
            mtime = stat(path).st_mtime
            diff = self.__last_mtime < mtime
            if diff > 0:
                LOGGER.info("Found new GeoIP Database, reopening", diff=diff)
                self.__open()
        except OSError as exc:
            LOGGER.warning("Failed to check GeoIP age", exc=exc)
            return

    @property
    def enabled(self) -> bool:
        """Check if GeoIP is enabled"""
        return bool(self.__reader)

    def city(self, ip_address: str) -> Optional[City]:
        """Wrapper for Reader.city"""
        with Hub.current.start_span(
            op="authentik.events.geo.city",
            description=ip_address,
        ):
            if not self.enabled:
                return None
            self.__check_expired()
            try:
                return self.__reader.city(ip_address)
            except (GeoIP2Error, ValueError):
                return None

    def city_to_dict(self, city: City) -> GeoIPDict:
        """Convert City to dict"""
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

    def city_dict(self, ip_address: str) -> Optional[GeoIPDict]:
        """Wrapper for self.city that returns a dict"""
        city = self.city(ip_address)
        if not city:
            return None
        return self.city_to_dict(city)


GEOIP_READER = GeoIPReader()
