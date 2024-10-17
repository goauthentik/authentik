"""events GeoIP Reader"""

from typing import TYPE_CHECKING, Optional, TypedDict

from django.http import HttpRequest
from geoip2.errors import GeoIP2Error
from geoip2.models import City
from sentry_sdk import start_span

from authentik.events.context_processors.mmdb import MMDBContextProcessor
from authentik.lib.config import CONFIG
from authentik.root.middleware import ClientIPMiddleware

if TYPE_CHECKING:
    from authentik.api.v3.config import Capabilities
    from authentik.events.models import Event


class GeoIPDict(TypedDict):
    """GeoIP Details"""

    continent: str
    country: str
    lat: float
    long: float
    city: str


class GeoIPContextProcessor(MMDBContextProcessor):
    """Slim wrapper around GeoIP API"""

    def capability(self) -> Optional["Capabilities"]:
        from authentik.api.v3.config import Capabilities

        return Capabilities.CAN_GEO_IP

    def path(self) -> str | None:
        return CONFIG.get("events.context_processors.geoip")

    def enrich_event(self, event: "Event"):
        city = self.city_dict(event.client_ip)
        if not city:
            return
        event.context["geo"] = city

    def enrich_context(self, request: HttpRequest) -> dict:
        # Different key `geoip` vs `geo` for legacy reasons
        return {"geoip": self.city_dict(ClientIPMiddleware.get_client_ip(request))}

    def city(self, ip_address: str) -> City | None:
        """Wrapper for Reader.city"""
        with start_span(
            op="authentik.events.geo.city",
            name=ip_address,
        ):
            if not self.configured():
                return None
            self.check_expired()
            try:
                return self.reader.city(ip_address)
            except (GeoIP2Error, ValueError):
                return None

    def city_to_dict(self, city: City | None) -> GeoIPDict:
        """Convert City to dict"""
        if not city:
            return {}
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

    def city_dict(self, ip_address: str) -> GeoIPDict | None:
        """Wrapper for self.city that returns a dict"""
        city = self.city(ip_address)
        if not city:
            return None
        return self.city_to_dict(city)


GEOIP_CONTEXT_PROCESSOR = GeoIPContextProcessor()
