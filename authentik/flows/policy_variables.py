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
    attribute,
    context_key,
    registry,
)
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.exceptions import PolicyException
from authentik.policies.types import PolicyRequest

FACT_FLOW_PLAN = "flow_plan"

registry.fact(
    FACT_FLOW_PLAN,
    _("Flow plan"),
    _("The flow being executed and the data collected by it so far."),
)
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

_PLAN = [FACT_FLOW_PLAN]


def _flow(request: PolicyRequest) -> Flow | None:
    if isinstance(request.obj, Flow):
        return request.obj
    if isinstance(request.obj, FlowStageBinding):
        return request.obj.target
    return None


registry.add_variable("flow.slug", _("Flow slug"), T.STRING, _PLAN, attribute(_flow, "slug"))
registry.add_variable(
    "flow.designation",
    _("Flow designation"),
    T.enum(FlowDesignation.choices),
    _PLAN,
    attribute(_flow, "designation"),
)
registry.add_variable(
    "plan.is_sso",
    _("Is SSO flow"),
    T.BOOLEAN,
    _PLAN,
    context_key(PLAN_CONTEXT_SSO, False),
    description=_("True when the flow was started by a source."),
)


@registry.variable(
    "plan.is_restored",
    _("Is restored"),
    T.BOOLEAN,
    requires=_PLAN,
    description=_(
        "True when the flow was restored, for example from an email link. Not set when the "
        "flow has not been restored."
    ),
)
def plan_is_restored(request: PolicyRequest):
    if PLAN_CONTEXT_IS_RESTORED not in request.context:
        return MISSING
    return bool(request.context[PLAN_CONTEXT_IS_RESTORED])


registry.add_variable(
    "plan.pending_user_authenticated",
    _("User already authenticated"),
    T.BOOLEAN,
    _PLAN,
    lambda request: hasattr(request.context.get(PLAN_CONTEXT_PENDING_USER), "backend"),
    description=_(
        "True when the user was already authenticated earlier in this flow, for example by "
        "an identification stage with a password field, a source or a passwordless login."
    ),
)
registry.add_variable(
    "plan.is_redirected",
    _("Is redirected"),
    T.BOOLEAN,
    _PLAN,
    lambda request: bool(request.context.get(PLAN_CONTEXT_IS_REDIRECTED)),
)
registry.add_variable(
    "plan.application",
    _("Application being authorized"),
    T.model("authentik_core.application"),
    _PLAN,
    context_key(PLAN_CONTEXT_APPLICATION, instance_of=Application),
)
registry.add_variable(
    "plan.source",
    _("Source"),
    T.model("authentik_core.source"),
    _PLAN,
    context_key(PLAN_CONTEXT_SOURCE, instance_of=Source),
    description=_("Source the user is authenticating or enrolling with."),
)
registry.add_variable(
    "plan.context",
    _("Flow context value"),
    T.ANY,
    _PLAN,
    lambda request, key: request.context.get(key, MISSING),
    param=ParamKind.KEY,
    description=_("Value of the flow context with the given key."),
)
registry.add_variable(
    "plan.user_switch_active",
    _("Is user switch"),
    T.BOOLEAN,
    _PLAN,
    lambda request: bool(request.context.get(PLAN_CONTEXT_USER_SWITCH_FROM_USER)),
    description=_("True when the flow switches to another user logged in on this browser."),
)


@registry.variable(
    "plan.user_switch_target_last_used",
    _("User switch target last used"),
    T.DATETIME,
    requires=_PLAN,
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
    last_used = (
        target_sessions(request.http_request, user.pk, session_key)
        .aggregate(last_used=Max("session__last_used"))
        .get("last_used")
    )
    return last_used or MISSING


def plan_for_request(request: PolicyRequest) -> FlowPlan:
    """The flow plan of the flow being executed, to modify its context"""
    plan = request.context.get("flow_plan")
    if not isinstance(plan, FlowPlan):
        raise PolicyException("Values can only be set while a flow is being executed")
    return plan


def set_plan_context(request: PolicyRequest, key: str, value: Any):
    """Set a key in the context of the flow being executed, and in the policy request so that
    later actions see the new value"""
    plan_for_request(request).context[key] = value
    request.context[key] = value


@registry.setter(
    "plan.context",
    _("Flow context value"),
    T.ANY,
    requires=_PLAN,
    param=ParamKind.KEY,
    description=_("Set a key in the context of the flow being executed."),
)
def setter_plan_context(request: PolicyRequest, key: str, value: Any):
    set_plan_context(request, key, value)
