"""Policy variables provided by the email stage"""

from django.utils.translation import gettext_lazy as _

from authentik.flows.policy_variables import FACT_FLOW_PLAN, set_plan_context
from authentik.policies.conditional.registry import registry
from authentik.policies.conditional.types import T
from authentik.policies.types import PolicyRequest
from authentik.stages.email.stage import PLAN_CONTEXT_EMAIL_OVERRIDE


@registry.setter(
    "plan.email_override",
    _("Send email to"),
    T.STRING,
    requires=[FACT_FLOW_PLAN],
    description=_("Email address the email stage sends to, instead of the user's email address."),
)
def setter_email_override(request: PolicyRequest, value: str):
    set_plan_context(request, PLAN_CONTEXT_EMAIL_OVERRIDE, value)
