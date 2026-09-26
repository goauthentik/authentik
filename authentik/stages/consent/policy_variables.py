"""Policy variables provided by the consent stage"""

from django.utils.translation import gettext_lazy as _

from authentik.flows.policy_variables import FACT_FLOW_PLAN, set_plan_context
from authentik.policies.conditional.registry import registry
from authentik.policies.conditional.types import T
from authentik.policies.types import PolicyRequest
from authentik.stages.consent.stage import PLAN_CONTEXT_CONSENT_HEADER


@registry.setter(
    "plan.consent_header",
    _("Consent header"),
    T.STRING,
    requires=[FACT_FLOW_PLAN],
    description=_("Text shown at the top of the consent stage."),
)
def setter_consent_header(request: PolicyRequest, value: str):
    set_plan_context(request, PLAN_CONTEXT_CONSENT_HEADER, value)
