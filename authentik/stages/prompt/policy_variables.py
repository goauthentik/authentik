"""Policy variables provided by the prompt stage"""

from django.utils.translation import gettext_lazy as _

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
registry.target("authentik_stages_prompt.promptstage", [FACT_HTTP_REQUEST, FACT_PROMPT_DATA])
# Prompt data is stored in the flow context, and available to all later policies
registry.target("authentik_flows.flow", [FACT_PROMPT_DATA])
registry.target("authentik_flows.flowstagebinding", [FACT_PROMPT_DATA])


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
