"""User switch view"""

from typing import Any, cast

from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.utils.translation import gettext as _

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


def user_switch_response(request: HttpRequest, user_pk: int) -> HttpResponse:
    """Authenticate another login held by this browser."""
    flow = request.brand.flow_user_switch
    if not flow:
        return bad_request_message(
            request,
            _("User switching is disabled."),
            title=_("User switching disabled"),
        )
    if not flow_applicable_to_current_user(request, flow):
        return HttpResponseNotFound()
    context = {}
    session = get_user_switching_session(request, user_pk)
    if not session:
        return HttpResponseNotFound()
    context[PLAN_CONTEXT_PENDING_USER] = session.user
    # Pre-fill the identification stage so the target user doesn't have to be retyped.
    context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = session.user.username
    context[PLAN_CONTEXT_USER_SWITCH_FROM_USER] = request.user
    context[PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION] = session.session.session_key
    return redirect_to_flow(request, flow, context)


def user_add_response(request: HttpRequest) -> HttpResponse:
    """Start an explicit additional-user login for this browser."""
    if not request.brand.flow_user_switch:
        return bad_request_message(
            request,
            _("User switching is disabled."),
            title=_("User switching disabled"),
        )
    flow = ToDefaultFlow.get_flow(request, FlowDesignation.AUTHENTICATION)
    return redirect_to_flow(request, flow, {PLAN_CONTEXT_USER_SWITCH_ADD_USER: True})


def redirect_to_flow(
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


def flow_applicable_to_current_user(request: HttpRequest, flow: Flow) -> bool:
    """Reject switch flows that the current source user cannot access."""
    engine = PolicyEngine(flow, cast(User, request.user), request)
    engine.use_cache = False
    engine.build()
    return engine.result.passing


def get_user_switching_session(request: HttpRequest, user_pk: int) -> AuthenticatedSession | None:
    """Live login bound to this request's user switching token, if any."""
    user_switching_token = getattr(request, "user_switching_token", None)
    if not user_switching_token:
        return None
    return (
        AuthenticatedSession.objects.filter(
            user_switching_token=user_switching_token,
            session__expires__gt=timezone.now(),
            user__is_active=True,
            user_id=user_pk,
        )
        .select_related("session", "user")
        .order_by("-session__last_used")
        .first()
    )


def get_user_switching_sessions(request: HttpRequest) -> list[AuthenticatedSession]:
    """Return the newest live login for each user held by this browser."""
    user_switching_token = getattr(request, "user_switching_token", None)
    if not user_switching_token:
        return []
    sessions = (
        AuthenticatedSession.objects.filter(
            user_switching_token=user_switching_token,
            session__expires__gt=timezone.now(),
            user__is_active=True,
        )
        .select_related("session", "user")
        .order_by("-is_current", "-session__last_used")
    )
    users = set()
    latest_sessions = []
    for session in sessions:
        if session.user_id in users:
            continue
        users.add(session.user_id)
        latest_sessions.append(session)
    return latest_sessions
