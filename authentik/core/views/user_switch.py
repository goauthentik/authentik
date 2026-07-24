"""User switch view"""

from typing import Any, cast

from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.utils.translation import gettext as _
from django.views import View

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession, User
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowDesignation
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


class UserSwitchView(View):
    """Authenticate another login held by this browser."""

    def post(self, request: HttpRequest, user_pk: int) -> HttpResponse:
        if request.user.pk == user_pk:
            return HttpResponseNotFound()
        flow = request.brand.flow_user_switch
        if not flow:
            return _disabled_response(request)
        if not _flow_applicable_to_current_user(request, flow):
            return HttpResponseNotFound()
        session = _get_user_switching_session(request, user_pk)
        if not session:
            return HttpResponseNotFound()
        return _redirect_to_flow(
            request,
            flow,
            {
                PLAN_CONTEXT_PENDING_USER: session.user,
                PLAN_CONTEXT_PENDING_USER_IDENTIFIER: session.user.username,
                PLAN_CONTEXT_USER_SWITCH_FROM_USER: request.user,
                PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION: session.session_id,
            },
        )


class UserAddView(View):
    """Start an explicit additional-user login for this browser."""

    def post(self, request: HttpRequest) -> HttpResponse:
        if not request.brand.flow_user_switch:
            return _disabled_response(request)
        flow = ToDefaultFlow.get_flow(request, FlowDesignation.AUTHENTICATION)
        return _redirect_to_flow(request, flow, {PLAN_CONTEXT_USER_SWITCH_ADD_USER: True})


def _disabled_response(request: HttpRequest) -> HttpResponse:
    return bad_request_message(
        request,
        _("User switching is disabled."),
        title=_("User switching disabled"),
    )


def _redirect_to_flow(
    request: HttpRequest,
    flow: Flow,
    context: dict[str, Any],
) -> HttpResponse:
    """Plan and redirect to the user switch flow."""
    planner = FlowPlanner(flow)
    # The user-switch context can change policy decisions while building the stage list.
    # Reusing a cached plan would skip that planning pass.
    planner.use_cache = False
    try:
        plan = planner.plan(request, context)
    except FlowNonApplicableException:
        return HttpResponseNotFound()
    return plan.to_redirect(request, flow)


def _flow_applicable_to_current_user(request: HttpRequest, flow: Flow) -> bool:
    """Reject switch flows that the current source user cannot access."""
    engine = PolicyEngine(flow, cast(User, request.user), request)
    engine.use_cache = False
    engine.build()
    return engine.result.passing


def _get_user_switching_session(request: HttpRequest, user_pk: int) -> AuthenticatedSession | None:
    """Live login bound to this request's user switching token, if any."""
    user_switching_token = getattr(request, "user_switching_token", None)
    if not user_switching_token:
        return None
    return (
        user_switching.live_sessions(user_switching_token)
        .filter(user_id=user_pk)
        .select_related("session", "user")
        .order_by("-session__last_used")
        .first()
    )


def get_user_switching_sessions(request: HttpRequest) -> list[AuthenticatedSession]:
    """Return the newest live login for each user held by this browser."""
    user_switching_token = getattr(request, "user_switching_token", None)
    if not user_switching_token:
        return []
    return list(
        user_switching.live_sessions(user_switching_token)
        .select_related("session", "user")
        .order_by("user_id", "-session__last_used")
        .distinct("user_id")
    )
