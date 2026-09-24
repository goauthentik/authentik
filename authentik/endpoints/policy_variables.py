"""Policy variables provided by endpoint devices"""

from django.utils.translation import gettext_lazy as _

from authentik.endpoints.facts import DeviceFacts
from authentik.endpoints.models import Device
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.policy_variables import FACT_FLOW_PLAN
from authentik.policies.conditional.registry import (
    FACT_HTTP_REQUEST,
    ParamKind,
    known_params_from_serializer,
    registry,
)
from authentik.policies.conditional.types import MISSING, T, dig
from authentik.policies.types import PolicyRequest

FACT_DEVICE = "device"

registry.fact(
    FACT_DEVICE,
    _("Device"),
    _("The endpoint device the user is authenticating from, or which is being accessed."),
)
registry.scenario(
    "device_access",
    [FACT_HTTP_REQUEST, FACT_DEVICE],
    models=["authentik_endpoints.device"],
    label=_("Device access"),
    description=_("Deciding whether a user can log in to an endpoint device."),
)
_DEVICE = [FACT_DEVICE, FACT_FLOW_PLAN]


def _device(request: PolicyRequest) -> Device | None:
    if isinstance(request.obj, Device):
        return request.obj
    device = request.context.get(PLAN_CONTEXT_DEVICE)
    return device if isinstance(device, Device) else None


@registry.variable(
    "device.name",
    _("Device name"),
    T.STRING,
    requires=_DEVICE,
    description=_("Name of the endpoint device. Not set when no device is known."),
)
def device_name(request: PolicyRequest):
    device = _device(request)
    return device.name if device else MISSING


@registry.variable(
    "device.facts",
    _("Device fact"),
    T.ANY,
    requires=_DEVICE,
    param=ParamKind.PATH,
    params=known_params_from_serializer(DeviceFacts()),
    description=_(
        "Fact reported for the endpoint device at the given dotted path, for example "
        "'hardware.manufacturer' or 'os.family'."
    ),
)
def device_facts(request: PolicyRequest, path: str):
    device = _device(request)
    if not device:
        return MISSING
    return dig(device.cached_facts.data, path)
