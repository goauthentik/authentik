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
from authentik.policies.conditional.registry import FACT_HTTP_REQUEST, ParamKind, registry
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.exceptions import PolicyException
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
    description=_(
        "True when the flow was restored, for example from an email link. Not set when the "
        "flow has not been restored."
    ),
)
def plan_is_restored(request: PolicyRequest):
    if PLAN_CONTEXT_IS_RESTORED not in request.context:
        return MISSING
    return bool(request.context[PLAN_CONTEXT_IS_RESTORED])


@registry.variable(
    "plan.pending_user_authenticated",
    _("User already authenticated"),
    T.BOOLEAN,
    requires=_PLAN,
    description=_(
        "True when the user was already authenticated earlier in this flow, for example by "
        "an identification stage with a password field, a source or a passwordless login."
    ),
)
def plan_pending_user_authenticated(request: PolicyRequest):
    return hasattr(request.context.get(PLAN_CONTEXT_PENDING_USER), "backend")


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


@registry.variable(
    "plan.user_switch_active",
    _("Is user switch"),
    T.BOOLEAN,
    requires=_PLAN,
    description=_("True when the flow switches to another user logged in on this browser."),
)
def plan_user_switch_active(request: PolicyRequest):
    return bool(request.context.get(PLAN_CONTEXT_USER_SWITCH_FROM_USER))


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
