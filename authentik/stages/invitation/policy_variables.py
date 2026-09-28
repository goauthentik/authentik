"""Policy variables provided by the invitation stage"""

from django.utils.translation import gettext_lazy as _

from authentik.flows.policy_variables import FACT_FLOW_PLAN
from authentik.policies.conditional.registry import ParamKind, registry
from authentik.policies.conditional.types import MISSING, T, dig
from authentik.policies.types import PolicyRequest
from authentik.stages.invitation.models import Invitation
from authentik.stages.invitation.stage import (
    PLAN_CONTEXT_INVITATION,
    PLAN_CONTEXT_INVITATION_IN_EFFECT,
)

registry.add_variable(
    "invitation.in_effect",
    _("Invitation used"),
    T.BOOLEAN,
    [FACT_FLOW_PLAN],
    lambda request: bool(request.context.get(PLAN_CONTEXT_INVITATION_IN_EFFECT)),
    description=_("True when the user is enrolling with an invitation."),
)


@registry.variable(
    "invitation.fixed_data",
    _("Invitation data"),
    T.ANY,
    requires=[FACT_FLOW_PLAN],
    param=ParamKind.PATH,
    description=_("Value of the invitation's fixed data at the given dotted path."),
)
def invitation_fixed_data(request: PolicyRequest, path: str):
    invitation = request.context.get(PLAN_CONTEXT_INVITATION)
    if not isinstance(invitation, Invitation):
        return MISSING
    return dig(invitation.fixed_data, path)
