"""Base event enricher"""

from functools import cache
from typing import TYPE_CHECKING

from django.http import HttpRequest

if TYPE_CHECKING:
    from authentik.api.v3.config import Capabilities
    from authentik.events.models import Event


class EventContextProcessor:
    """Base event enricher"""

    def capability(self) -> Capabilities | None:
        """Return the capability this context processor provides"""
        return None

    def configured(self) -> bool:
        """Return true if this context processor is configured"""
        return False

    def enrich_event(self, event: Event):
        """Modify event"""
        raise NotImplementedError

    def enrich_context(self, request: HttpRequest) -> dict:
        """Modify context"""
        raise NotImplementedError


@cache
def get_context_processors() -> list[EventContextProcessor]:
    """Get a list of all configured context processors"""
    from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR
    from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR

    processors_types = [ASN_CONTEXT_PROCESSOR, GEOIP_CONTEXT_PROCESSOR]
    processors = []
    for _type in processors_types:
        if _type.configured():
            processors.append(_type)
    return processors
