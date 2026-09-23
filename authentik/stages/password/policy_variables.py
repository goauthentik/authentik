"""Policy variables provided by the password stage"""

from django.utils.translation import gettext_lazy as _

from authentik.flows.policy_variables import FACT_FLOW_PLAN
from authentik.policies.conditional.registry import ParamKind, registry
from authentik.policies.conditional.types import MISSING, T, dig
from authentik.policies.types import PolicyRequest
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS


@registry.variable(
    "plan.auth_method",
    _("Authentication method"),
    T.STRING,
    requires=[FACT_FLOW_PLAN],
    description=_("How the user authenticated, for example 'password', 'auth_mfa' or 'token'."),
)
def plan_auth_method(request: PolicyRequest):
    return request.context.get(PLAN_CONTEXT_METHOD, MISSING)


@registry.variable(
    "plan.auth_method_args",
    _("Authentication method arguments"),
    T.ANY,
    requires=[FACT_FLOW_PLAN],
    param=ParamKind.PATH,
    description=_("Details of the authentication method at the given dotted path."),
)
def plan_auth_method_args(request: PolicyRequest, path: str):
    return dig(request.context.get(PLAN_CONTEXT_METHOD_ARGS), path)
