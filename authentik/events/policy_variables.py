"""Policy variables provided by events"""

from django.utils.translation import gettext_lazy as _

from authentik.events.models import Event, EventAction
from authentik.policies.conditional.registry import FACT_HTTP_REQUEST, ParamKind, registry
from authentik.policies.conditional.types import MISSING, T, dig
from authentik.policies.types import PolicyRequest

FACT_EVENT = "event"

registry.fact(
    FACT_EVENT,
    _("Event"),
    _("The event which triggered a notification rule."),
)
registry.scenario(
    "notification_rule",
    [FACT_EVENT],
    models=["authentik_events.notificationrule"],
    label=_("Notification rule"),
    description=_("Deciding whether an event triggers a notification."),
)


def _context_value(request: PolicyRequest, key: str, path: str):
    """Get a value from the data added by context processors (GeoIP/ASN)"""
    return dig(request.context.get(key) or {}, path)


@registry.variable(
    "request.geoip.country",
    _("Country"),
    T.STRING,
    requires=[FACT_HTTP_REQUEST],
    description=_("ISO country code of the client IP, when GeoIP is configured."),
)
def geoip_country(request: PolicyRequest):
    return _context_value(request, "geoip", "country")


@registry.variable(
    "request.geoip.continent",
    _("Continent"),
    T.STRING,
    requires=[FACT_HTTP_REQUEST],
    description=_("Continent code of the client IP, when GeoIP is configured."),
)
def geoip_continent(request: PolicyRequest):
    return _context_value(request, "geoip", "continent")


@registry.variable(
    "request.geoip.city",
    _("City"),
    T.STRING,
    requires=[FACT_HTTP_REQUEST],
    description=_("City of the client IP, when GeoIP is configured."),
)
def geoip_city(request: PolicyRequest):
    return _context_value(request, "geoip", "city")


@registry.variable(
    "request.asn.asn",
    _("ASN"),
    T.NUMBER,
    requires=[FACT_HTTP_REQUEST],
    description=_("Autonomous system number of the client IP, when ASN is configured."),
)
def asn_asn(request: PolicyRequest):
    return _context_value(request, "asn", "asn")


@registry.variable(
    "request.asn.as_org",
    _("AS organization"),
    T.STRING,
    requires=[FACT_HTTP_REQUEST],
    description=_("Organization of the autonomous system of the client IP."),
)
def asn_as_org(request: PolicyRequest):
    return _context_value(request, "asn", "as_org")


def _event(request: PolicyRequest) -> Event | None:
    event = request.context.get("event")
    return event if isinstance(event, Event) else None


@registry.variable(
    "event.action", _("Event action"), T.enum(EventAction.choices), requires=[FACT_EVENT]
)
def event_action(request: PolicyRequest):
    event = _event(request)
    return event.action if event else MISSING


@registry.variable(
    "event.app",
    _("Event app"),
    T.STRING,
    requires=[FACT_EVENT],
    description=_("Python module which created the event."),
)
def event_app(request: PolicyRequest):
    event = _event(request)
    return event.app if event else MISSING


@registry.variable(
    "event.model.app",
    _("Event model app"),
    T.STRING,
    requires=[FACT_EVENT],
    description=_("App label of the model the event relates to."),
)
def event_model_app(request: PolicyRequest):
    event = _event(request)
    return dig(event.context, "model.app") if event else MISSING


@registry.variable(
    "event.model.name",
    _("Event model name"),
    T.STRING,
    requires=[FACT_EVENT],
    description=_("Name of the model the event relates to."),
)
def event_model_name(request: PolicyRequest):
    event = _event(request)
    return dig(event.context, "model.model_name") if event else MISSING


@registry.variable("event.client_ip", _("Event client IP"), T.IP, requires=[FACT_EVENT])
def event_client_ip(request: PolicyRequest):
    event = _event(request)
    return (event.client_ip or MISSING) if event else MISSING


@registry.variable("event.created", _("Event created"), T.DATETIME, requires=[FACT_EVENT])
def event_created(request: PolicyRequest):
    event = _event(request)
    return event.created if event else MISSING


@registry.variable(
    "event.context",
    _("Event context"),
    T.ANY,
    requires=[FACT_EVENT],
    param=ParamKind.PATH,
    description=_("Value of the event's context at the given dotted path."),
)
def event_context(request: PolicyRequest, path: str):
    event = _event(request)
    return dig(event.context, path) if event else MISSING
