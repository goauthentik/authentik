"""Policy variables provided by the prompt stage"""

from typing import Any

from django.utils.translation import gettext_lazy as _

from authentik.core.models import User
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.policy_variables import FACT_FLOW_PLAN
from authentik.policies.conditional.registry import FACT_HTTP_REQUEST, ParamKind, registry
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.types import PolicyRequest
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

FACT_PROMPT_DATA = "prompt_data"

registry.fact(
    FACT_PROMPT_DATA,
    _("Prompt data"),
    _("Data entered by the user in a prompt stage."),
)
# Validation policies of a prompt stage are evaluated with only the prompt data
registry.scenario(
    "prompt_validation",
    [FACT_HTTP_REQUEST, FACT_PROMPT_DATA],
    models=["authentik_stages_prompt.promptstage"],
    label=_("Prompt validation"),
    description=_("Validating the data a user entered in a prompt stage."),
)
# Prompt data is stored in the flow context, and available to all later policies
registry.scenario("flow_execution", [FACT_PROMPT_DATA])
registry.scenario("flow_stage_execution", [FACT_PROMPT_DATA])


@registry.variable(
    "prompt_data",
    _("Prompt field"),
    T.ANY,
    requires=[FACT_PROMPT_DATA],
    param=ParamKind.KEY,
    description=_("Value the user entered in the prompt field with the given field key."),
)
def prompt_data(request: PolicyRequest, key: str):
    data = request.context.get(PLAN_CONTEXT_PROMPT)
    if not isinstance(data, dict):
        return MISSING
    return data.get(key, MISSING)


@registry.variable(
    "prompt_data.email_in_use",
    _("Email address in use"),
    T.BOOLEAN,
    requires=[FACT_PROMPT_DATA],
    param=ParamKind.KEY,
    description=_(
        "True when the email address entered in the prompt field with the given field key is "
        "already used by another user."
    ),
)
def prompt_data_email_in_use(request: PolicyRequest, key: str):
    data = request.context.get(PLAN_CONTEXT_PROMPT)
    if not isinstance(data, dict) or not data.get(key):
        return MISSING
    query = User.objects.filter(email__iexact=data[key])
    pending_user = request.context.get(PLAN_CONTEXT_PENDING_USER)
    if pending_user and pending_user.pk:
        query = query.exclude(pk=pending_user.pk)
    elif request.user and request.user.is_authenticated:
        query = query.exclude(pk=request.user.pk)
    return query.exists()


@registry.setter(
    "prompt_data",
    _("Prompt field"),
    T.ANY,
    requires=[FACT_PROMPT_DATA, FACT_FLOW_PLAN],
    param=ParamKind.KEY,
    description=_(
        "Set the value of a prompt field, for example to use the email address as username."
    ),
)
def setter_prompt_data(request: PolicyRequest, key: str, value: Any):
    data = request.context.get(PLAN_CONTEXT_PROMPT)
    if not isinstance(data, dict):
        data = {}
        request.context[PLAN_CONTEXT_PROMPT] = data
    plan = request.context.get("flow_plan")
    if isinstance(plan, FlowPlan) and plan.context.get(PLAN_CONTEXT_PROMPT) is not data:
        plan.context.setdefault(PLAN_CONTEXT_PROMPT, {})[key] = value
    data[key] = value
