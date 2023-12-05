"""ASN Enricher"""
from os import stat
from typing import TYPE_CHECKING, Optional, TypedDict

from geoip2.database import Reader
from geoip2.errors import GeoIP2Error
from geoip2.models import ASN
from sentry_sdk import Hub
from structlog.stdlib import get_logger

from authentik.events.enrich.base import EventEnricher
from authentik.lib.config import CONFIG

if TYPE_CHECKING:
    from authentik.events.models import Event
LOGGER = get_logger()


class ASNDict(TypedDict):
    """ASN Details"""

    asn: int
    as_org: str | None
    network: str | None


class ASNEnricher(EventEnricher):
    """ASN Database reader wrapper"""

    def __init__(self):
        self.__reader: Optional[Reader] = None
        self.__last_mtime: float = 0.0
        self.__open()

    def enrich_event(self, event: "Event"):
        asn = self.asn_dict(event.client_ip)
        if not asn:
            return
        event.context["asn"] = asn

    @property
    def enabled(self) -> bool:
        """Check if GeoIP is enabled"""
        return bool(self.__reader)

    def __open(self):
        """Get ASN Reader, if configured, otherwise none"""
        path = CONFIG.get("events.processors.asn")
        if path == "" or not path:
            return
        try:
            self.__reader = Reader(path)
            self.__last_mtime = stat(path).st_mtime
            LOGGER.info("Loaded ASN database", last_write=self.__last_mtime)
        except OSError as exc:
            LOGGER.warning("Failed to load ASN database", exc=exc)

    def __check_expired(self):
        """Check if the modification date of the ASN database has
        changed, and reload it if so"""
        path = CONFIG.get("events.processors.asn")
        try:
            mtime = stat(path).st_mtime
            diff = self.__last_mtime < mtime
            if diff > 0:
                LOGGER.info("Found new ASN Database, reopening", diff=diff)
                self.__open()
        except OSError as exc:
            LOGGER.warning("Failed to check ASN age", exc=exc)
            return

    def asn(self, ip_address: str) -> Optional[ASN]:
        """Wrapper for Reader.asn"""
        with Hub.current.start_span(
            op="authentik.events.asn.asn",
            description=ip_address,
        ):
            if not self.enabled:
                return None
            self.__check_expired()
            try:
                return self.__reader.asn(ip_address)
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
