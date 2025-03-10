"""ASN Enricher"""

from typing import TYPE_CHECKING, Optional, TypedDict

from django.http import HttpRequest
from geoip2.errors import GeoIP2Error
from geoip2.models import ASN
from sentry_sdk import start_span

from authentik.events.context_processors.mmdb import MMDBContextProcessor
from authentik.lib.config import CONFIG
from authentik.root.middleware import ClientIPMiddleware

if TYPE_CHECKING:
    from authentik.api.v3.config import Capabilities
    from authentik.events.models import Event


class ASNDict(TypedDict):
    """ASN Details"""

    asn: int
    as_org: str | None
    network: str | None


class ASNContextProcessor(MMDBContextProcessor):
    """ASN Database reader wrapper"""

    def capability(self) -> Optional["Capabilities"]:
        from authentik.api.v3.config import Capabilities

        return Capabilities.CAN_ASN

    def path(self) -> str | None:
        return CONFIG.get("events.context_processors.asn")

    def enrich_event(self, event: "Event"):
        asn = self.asn_dict(event.client_ip)
        if not asn:
            return
        event.context["asn"] = asn

    def enrich_context(self, request: HttpRequest) -> dict:
        return {
            "asn": self.asn_dict(ClientIPMiddleware.get_client_ip(request)),
        }

    def asn(self, ip_address: str) -> ASN | None:
        """Wrapper for Reader.asn"""
        with start_span(
            op="authentik.events.asn.asn",
            name=ip_address,
        ):
            if not self.configured():
                return None
            self.check_expired()
            try:
                return self.reader.asn(ip_address)
            except (GeoIP2Error, ValueError):
                return None

    def asn_to_dict(self, asn: ASN | None) -> ASNDict:
        """Convert ASN to dict"""
        if not asn:
            return {}
        asn_dict: ASNDict = {
            "asn": asn.autonomous_system_number,
            "as_org": asn.autonomous_system_organization,
            "network": str(asn.network) if asn.network else None,
        }
        return asn_dict

    def asn_dict(self, ip_address: str) -> ASNDict | None:
        """Wrapper for self.asn that returns a dict"""
        asn = self.asn(ip_address)
        if not asn:
            return None
        return self.asn_to_dict(asn)


ASN_CONTEXT_PROCESSOR = ASNContextProcessor()
