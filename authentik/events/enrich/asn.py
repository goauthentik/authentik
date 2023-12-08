"""ASN Enricher"""
from typing import TYPE_CHECKING, Optional, TypedDict

from geoip2.errors import GeoIP2Error
from geoip2.models import ASN
from sentry_sdk import Hub

from authentik.events.enrich.mmdb import MMDBEnricher
from authentik.lib.config import CONFIG

if TYPE_CHECKING:
    from authentik.events.models import Event


class ASNDict(TypedDict):
    """ASN Details"""

    asn: int
    as_org: str | None
    network: str | None


class ASNEnricher(MMDBEnricher):
    """ASN Database reader wrapper"""

    def path(self) -> str | None:
        return CONFIG.get("events.processors.asn")

    def enrich_event(self, event: "Event"):
        asn = self.asn_dict(event.client_ip)
        if not asn:
            return
        event.context["asn"] = asn

    def asn(self, ip_address: str) -> Optional[ASN]:
        """Wrapper for Reader.asn"""
        with Hub.current.start_span(
            op="authentik.events.asn.asn",
            description=ip_address,
        ):
            if not self.enabled:
                return None
            self.check_expired()
            try:
                return self.reader.asn(ip_address)
            except (GeoIP2Error, ValueError):
                return None

    def asn_to_dict(self, asn: ASN) -> ASNDict:
        """Convert ASN to dict"""
        asn_dict: ASNDict = {
            "asn": asn.autonomous_system_number,
            "as_org": asn.autonomous_system_organization,
            "network": str(asn.network) if asn.network else None,
        }
        return asn_dict

    def asn_dict(self, ip_address: str) -> Optional[ASNDict]:
        """Wrapper for self.asn that returns a dict"""
        asn = self.asn(ip_address)
        if not asn:
            return None
        return self.asn_to_dict(asn)


ASN_ENRICHER = ASNEnricher()
