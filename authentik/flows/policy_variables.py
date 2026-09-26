"""Policy variables provided by flows"""

from typing import Any

from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from authentik.core.models import Application, Source
from authentik.core.user_switching import target_sessions
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_IS_REDIRECTED,
    PLAN_CONTEXT_IS_RESTORED,
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    PLAN_CONTEXT_USER_SWITCH_FROM_USER,
    PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION,
    FlowPlan,
)
from authentik.policies.conditional.registry import (
    FACT_HTTP_REQUEST,
    ParamKind,
    Variable,
    registry,
)
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.exceptions import PolicyException
from authentik.policies.types import PolicyRequest

FACT_FLOW_PLAN = "flow_plan"

registry.scenario(
    "flow_execution",
    [FACT_HTTP_REQUEST, FACT_FLOW_PLAN],
    models=["authentik_flows.flow"],
    label=_("Flow execution"),
    description=_("Deciding whether a flow can be used, when it's started."),
)
registry.scenario(
    "flow_stage_execution",
    [FACT_HTTP_REQUEST, FACT_FLOW_PLAN],
    models=["authentik_flows.flowstagebinding"],
    label=_("Flow stage execution"),
    description=_("Deciding whether a stage of a flow runs, and preparing values for it."),
)


def _flow(request: PolicyRequest) -> Flow | None:
    if isinstance(request.obj, FlowStageBinding):
        return request.obj.target
    return request.obj if isinstance(request.obj, Flow) else None


registry.variable("flow.slug", _("Flow slug"), T.STRING, [FACT_FLOW_PLAN])(
    Variable.attribute(_flow, "slug")
)
registry.variable(
    "flow.designation", _("Flow designation"), T.enum(FlowDesignation.choices), [FACT_FLOW_PLAN]
)(Variable.attribute(_flow, "designation"))
registry.variable(
    "plan.is_sso",
    _("Is SSO flow"),
    T.BOOLEAN,
    [FACT_FLOW_PLAN],
    description=_("True when the flow was started by a source."),
)(Variable.context(PLAN_CONTEXT_SSO, False))
registry.variable(
    "plan.is_restored",
    _("Is restored"),
    T.BOOLEAN,
    [FACT_FLOW_PLAN],
    description=_(
        "True when the flow was restored, for example from an email link. Not set when the "
        "flow has not been restored."
    ),
)(
    lambda request: (
        bool(request.context[PLAN_CONTEXT_IS_RESTORED])
        if PLAN_CONTEXT_IS_RESTORED in request.context
        else MISSING
    )
)
registry.variable(
    "plan.pending_user_authenticated",
    _("User already authenticated"),
    T.BOOLEAN,
    [FACT_FLOW_PLAN],
    description=_(
        "True when the user was already authenticated earlier in this flow, for example by "
        "an identification stage with a password field, a source or a passwordless login."
    ),
)(lambda request: hasattr(request.context.get(PLAN_CONTEXT_PENDING_USER), "backend"))
registry.variable("plan.is_redirected", _("Is redirected"), T.BOOLEAN, [FACT_FLOW_PLAN])(
    lambda request: bool(request.context.get(PLAN_CONTEXT_IS_REDIRECTED))
)
registry.variable(
    "plan.application",
    _("Application being authorized"),
    T.model("authentik_core.application"),
    [FACT_FLOW_PLAN],
)(Variable.context(PLAN_CONTEXT_APPLICATION, instance_of=Application))
registry.variable(
    "plan.source",
    _("Source"),
    T.model("authentik_core.source"),
    [FACT_FLOW_PLAN],
    description=_("Source the user is authenticating or enrolling with."),
)(Variable.context(PLAN_CONTEXT_SOURCE, instance_of=Source))
registry.variable(
    "plan.context",
    _("Flow context value"),
    T.ANY,
    [FACT_FLOW_PLAN],
    param=ParamKind.KEY,
    description=_("Value of the flow context with the given key."),
)(lambda request, key: request.context.get(key, MISSING))
registry.variable(
    "plan.user_switch_active",
    _("Is user switch"),
    T.BOOLEAN,
    [FACT_FLOW_PLAN],
    description=_("True when the flow switches to another user logged in on this browser."),
)(lambda request: bool(request.context.get(PLAN_CONTEXT_USER_SWITCH_FROM_USER)))


@registry.variable(
    "plan.user_switch_target_last_used",
    _("User switch target last used"),
    T.DATETIME,
    [FACT_FLOW_PLAN],
    description=_(
        "When the session of the user being switched to was last used. Not set when the flow "
        "is not a user switch."
    ),
)
def plan_user_switch_target_last_used(request: PolicyRequest):
    user = request.context.get(PLAN_CONTEXT_PENDING_USER)
    session_key = request.context.get(PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION)
    if not request.http_request or not user or not session_key:
        return MISSING
    sessions = target_sessions(request.http_request, user.pk, session_key)
    return sessions.aggregate(last_used=Max("session__last_used"))["last_used"] or MISSING


@registry.setter(
    "plan.context",
    _("Flow context value"),
    T.ANY,
    [FACT_FLOW_PLAN],
    param=ParamKind.KEY,
    description=_("Set a key in the context of the flow being executed."),
)
def set_plan_context(request: PolicyRequest, key: str, value: Any):
    """Set a key in the context of the flow being executed, and in the policy request so that
    later actions see the new value"""
    plan = request.context.get("flow_plan")
    if not isinstance(plan, FlowPlan):
        raise PolicyException("Values can only be set while a flow is being executed")
    plan.context[key] = value
    request.context[key] = value
