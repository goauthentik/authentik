"""Policy variables provided by flows"""

from django.utils.translation import gettext_lazy as _

from authentik.core.models import Application, Source
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_IS_REDIRECTED,
    PLAN_CONTEXT_IS_RESTORED,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
)
from authentik.policies.conditional.registry import FACT_HTTP_REQUEST, ParamKind, registry
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.types import PolicyRequest

FACT_FLOW_PLAN = "flow_plan"

registry.fact(
    FACT_FLOW_PLAN,
    _("Flow plan"),
    _("The flow being executed and the data collected by it so far."),
)
registry.target("authentik_flows.flow", [FACT_HTTP_REQUEST, FACT_FLOW_PLAN])
registry.target("authentik_flows.flowstagebinding", [FACT_HTTP_REQUEST, FACT_FLOW_PLAN])

_PLAN = [FACT_FLOW_PLAN]


def _flow(request: PolicyRequest) -> Flow | None:
    if isinstance(request.obj, Flow):
        return request.obj
    if isinstance(request.obj, FlowStageBinding):
        return request.obj.target
    return None


@registry.variable("flow.slug", _("Flow slug"), T.STRING, requires=_PLAN)
def flow_slug(request: PolicyRequest):
    flow = _flow(request)
    return flow.slug if flow else MISSING


@registry.variable(
    "flow.designation", _("Flow designation"), T.enum(FlowDesignation.choices), requires=_PLAN
)
def flow_designation(request: PolicyRequest):
    flow = _flow(request)
    return flow.designation if flow else MISSING


@registry.variable(
    "plan.is_sso",
    _("Is SSO flow"),
    T.BOOLEAN,
    requires=_PLAN,
    description=_("True when the flow was started by a source."),
)
def plan_is_sso(request: PolicyRequest):
    return request.context.get(PLAN_CONTEXT_SSO, False)


@registry.variable(
    "plan.is_restored",
    _("Is restored"),
    T.BOOLEAN,
    requires=_PLAN,
    description=_("True when the flow was restored, for example from an email link."),
)
def plan_is_restored(request: PolicyRequest):
    return bool(request.context.get(PLAN_CONTEXT_IS_RESTORED, False))


@registry.variable("plan.is_redirected", _("Is redirected"), T.BOOLEAN, requires=_PLAN)
def plan_is_redirected(request: PolicyRequest):
    return bool(request.context.get(PLAN_CONTEXT_IS_REDIRECTED, False))


@registry.variable(
    "plan.application",
    _("Application being authorized"),
    T.model("authentik_core.application"),
    requires=_PLAN,
)
def plan_application(request: PolicyRequest):
    app = request.context.get(PLAN_CONTEXT_APPLICATION)
    return app if isinstance(app, Application) else MISSING


@registry.variable(
    "plan.source",
    _("Source"),
    T.model("authentik_core.source"),
    requires=_PLAN,
    description=_("Source the user is authenticating or enrolling with."),
)
def plan_source(request: PolicyRequest):
    source = request.context.get(PLAN_CONTEXT_SOURCE)
    return source if isinstance(source, Source) else MISSING


@registry.variable(
    "plan.context",
    _("Flow context value"),
    T.ANY,
    requires=_PLAN,
    param=ParamKind.KEY,
    description=_("Value of the flow context with the given key."),
)
def plan_context(request: PolicyRequest, key: str):
    return request.context.get(key, MISSING)
