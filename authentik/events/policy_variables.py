"""Policy variables provided by events"""

from django.utils.translation import gettext_lazy as _

from authentik.events.models import Event, EventAction
from authentik.policies.conditional.registry import (
    FACT_HTTP_REQUEST,
    ParamKind,
    attribute,
    registry,
)
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


for _key, _label, _type, _description in (
    (
        "geoip.country",
        _("Country"),
        T.STRING,
        _("ISO country code of the client IP, when GeoIP is configured."),
    ),
    (
        "geoip.continent",
        _("Continent"),
        T.STRING,
        _("Continent code of the client IP, when GeoIP is configured."),
    ),
    ("geoip.city", _("City"), T.STRING, _("City of the client IP, when GeoIP is configured.")),
    (
        "asn.asn",
        _("ASN"),
        T.NUMBER,
        _("Autonomous system number of the client IP, when ASN is configured."),
    ),
    (
        "asn.as_org",
        _("AS organization"),
        T.STRING,
        _("Organization of the autonomous system of the client IP."),
    ),
):
    # Added to the context by the GeoIP/ASN context processors
    registry.add_variable(
        f"request.{_key}",
        _label,
        _type,
        [FACT_HTTP_REQUEST],
        lambda request, key=_key: dig(request.context, key),
        description=_description,
    )


def _event(request: PolicyRequest) -> Event | None:
    event = request.context.get("event")
    return event if isinstance(event, Event) else None


def _event_context(request: PolicyRequest, path: str):
    event = _event(request)
    return dig(event.context, path) if event else MISSING


registry.add_variable(
    "event.action",
    _("Event action"),
    T.enum(EventAction.choices),
    [FACT_EVENT],
    attribute(_event, "action"),
)
registry.add_variable(
    "event.app",
    _("Event app"),
    T.STRING,
    [FACT_EVENT],
    attribute(_event, "app"),
    description=_("Python module which created the event."),
)
registry.add_variable(
    "event.model.app",
    _("Event model app"),
    T.STRING,
    [FACT_EVENT],
    lambda request: _event_context(request, "model.app"),
    description=_("App label of the model the event relates to."),
)
registry.add_variable(
    "event.model.name",
    _("Event model name"),
    T.STRING,
    [FACT_EVENT],
    lambda request: _event_context(request, "model.model_name"),
    description=_("Name of the model the event relates to."),
)
registry.add_variable(
    "event.client_ip",
    _("Event client IP"),
    T.IP,
    [FACT_EVENT],
    attribute(_event, "client_ip", blank_missing=True),
)
registry.add_variable(
    "event.created", _("Event created"), T.DATETIME, [FACT_EVENT], attribute(_event, "created")
)
registry.add_variable(
    "event.context",
    _("Event context"),
    T.ANY,
    [FACT_EVENT],
    _event_context,
    param=ParamKind.PATH,
    description=_("Value of the event's context at the given dotted path."),
)
