"""Policy variables provided by the password stage"""

from django.utils.translation import gettext_lazy as _

from authentik.flows.policy_variables import FACT_FLOW_PLAN
from authentik.policies.conditional.registry import ParamKind, context_key, registry
from authentik.policies.conditional.types import T, dig
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

registry.add_variable(
    "plan.auth_method",
    _("Authentication method"),
    T.STRING,
    [FACT_FLOW_PLAN],
    context_key(PLAN_CONTEXT_METHOD),
    description=_("How the user authenticated, for example 'password', 'auth_mfa' or 'token'."),
)
registry.add_variable(
    "plan.auth_method_args",
    _("Authentication method arguments"),
    T.ANY,
    [FACT_FLOW_PLAN],
    lambda request, path: dig(request.context.get(PLAN_CONTEXT_METHOD_ARGS), path),
    param=ParamKind.PATH,
    description=_("Details of the authentication method at the given dotted path."),
)
