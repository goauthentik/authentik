"""User-switch flow entry point."""

from typing import Any, cast

from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.utils.translation import gettext as _

from authentik.core import user_switching
from authentik.core.models import User
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import FlowDesignation
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_USER_SWITCH_ADD_USER,
    PLAN_CONTEXT_USER_SWITCH_FROM_USER,
    PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION,
    FlowPlanner,
)
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.views.executor import ToDefaultFlow
from authentik.lib.views import bad_request_message
from authentik.policies.engine import PolicyEngine


def start_user_switch_flow(request: HttpRequest, user_pk: int | None) -> HttpResponse:
    """Plan an add-user flow or a switch to a live session held by this browser."""
    if user_pk is not None and user_pk == request.user.pk:
        return HttpResponseNotFound()
    switch_flow = request.brand.flow_user_switch
    if not switch_flow:
        return bad_request_message(
            request,
            _("User switching is disabled."),
            title=_("User switching disabled"),
        )

    context: dict[str, Any]
    if user_pk is None:
        flow = ToDefaultFlow.get_flow(request, FlowDesignation.AUTHENTICATION)
        context = {PLAN_CONTEXT_USER_SWITCH_ADD_USER: True}
    else:
        flow = switch_flow
        engine = PolicyEngine(flow, cast(User, request.user), request)
        engine.use_cache = False
        engine.build()
        if not engine.result.passing:
            return HttpResponseNotFound()
        user_switching_token = getattr(request, "user_switching_token", None)
        if not user_switching_token:
            return HttpResponseNotFound()
        target = (
            user_switching.live_sessions(user_switching_token)
            .filter(user_id=user_pk)
            .select_related("session", "user")
            .order_by("-session__last_used")
            .first()
        )
        if not target:
            return HttpResponseNotFound()
        context = {
            PLAN_CONTEXT_PENDING_USER: target.user,
            PLAN_CONTEXT_PENDING_USER_IDENTIFIER: target.user.username,
            PLAN_CONTEXT_USER_SWITCH_FROM_USER: request.user,
            PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION: target.session_id,
        }

    planner = FlowPlanner(flow)
    # User-switch context affects policy decisions, so do not reuse a cached plan.
    planner.use_cache = False
    try:
        plan = planner.plan(request, context)
    except FlowNonApplicableException:
        return HttpResponseNotFound()
    return plan.to_redirect(request, flow)
