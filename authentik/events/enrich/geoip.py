"""events GeoIP Reader"""
from typing import TYPE_CHECKING, Optional, TypedDict

from geoip2.errors import GeoIP2Error
from geoip2.models import City
from sentry_sdk.hub import Hub

from authentik.events.enrich.mmdb import MMDBEnricher
from authentik.lib.config import CONFIG

if TYPE_CHECKING:
    from authentik.events.models import Event


class GeoIPDict(TypedDict):
    """GeoIP Details"""

    continent: str
    country: str
    lat: float
    long: float
    city: str


class GeoIPEnricher(MMDBEnricher):
    """Slim wrapper around GeoIP API"""

    def path(self) -> str | None:
        return CONFIG.get("events.processors.geoip")

    def enrich_event(self, event: "Event"):
        city = self.city_dict(event.client_ip)
        if not city:
            return
        event.context["geo"] = city

    def city(self, ip_address: str) -> Optional[City]:
        """Wrapper for Reader.city"""
        with Hub.current.start_span(
            op="authentik.events.geo.city",
            description=ip_address,
        ):
            if not self.enabled:
                return None
            self.check_expired()
            try:
                return self.reader.city(ip_address)
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


GEOIP_ENRICHER = GeoIPEnricher()
