"""Next action flows required after login"""

from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import USER_ATTRIBUTE_NEXT_ACTIONS, User
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, FlowDesignation, in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_REDIRECT,
    FlowPlan,
    FlowPlanner,
)
from authentik.flows.stage import StageView
from authentik.flows.views.executor import SESSION_KEY_PLAN

LOGGER = get_logger()
SESSION_KEY_PENDING_NEXT_ACTIONS = "authentik/stages/user_login/pending_next_actions"

# Flows that create or end a session cannot run as a next action
NEXT_ACTION_DISALLOWED_DESIGNATIONS = [
    FlowDesignation.AUTHENTICATION,
    FlowDesignation.INVALIDATION,
]

PENDING_ALLOWED_READ_PATHS = (
    "/api/v3/core/users/me/",
    "/api/v3/root/config/",
)
PENDING_ALLOWED_READ_PREFIXES = ("/static/", "/media/")


def next_actions_enabled() -> bool:
    """Whether next actions are enforced on this install. Any installed license counts,
    even an expired one, so a lapsed license cannot switch off mandatory actions."""
    from authentik.enterprise.license import LicenseKey
    from authentik.enterprise.models import LicenseUsageStatus

    return LicenseKey.cached_summary().status != LicenseUsageStatus.UNLICENSED


def next_action_slugs(value: Any) -> list[str]:
    """Normalize the next-actions attribute value to a list of slugs, without validation"""
    slugs = value if isinstance(value, list) else [value]
    return [slug for slug in slugs if isinstance(slug, str)]


def resolve_next_actions(value: Any) -> list[Flow]:
    """Resolve the value of the next-actions user attribute (a flow slug or
    a list of flow slugs) to flows. Raises ValueError for entries that don't
    resolve to a usable flow."""
    slugs = value if isinstance(value, list) else [value]
    flows = []
    for slug in slugs:
        if not isinstance(slug, str):
            raise ValueError(f"Invalid next action entry: {slug!r}")
        flow = Flow.objects.filter(slug=slug).first()
        if not flow:
            raise ValueError(f"Next action flow does not exist: {slug}")
        if flow.designation in NEXT_ACTION_DISALLOWED_DESIGNATIONS:
            raise ValueError(f"Flow cannot be used as a next action: {slug}")
        flows.append(flow)
    return flows


class NextActionDoneStageView(StageView):
    """Remove a completed next action flow from the user's attributes"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        user: User = request.user
        slug = self.executor.current_stage.flow_slug
        value = user.attributes.get(USER_ATTRIBUTE_NEXT_ACTIONS)
        if isinstance(value, list):
            if slug in value:
                value.remove(slug)
            if not value:
                user.attributes.pop(USER_ATTRIBUTE_NEXT_ACTIONS, None)
        elif value == slug:
            user.attributes.pop(USER_ATTRIBUTE_NEXT_ACTIONS, None)
        if USER_ATTRIBUTE_NEXT_ACTIONS not in user.attributes:
            request.session.pop(SESSION_KEY_PENDING_NEXT_ACTIONS, None)
        with audit_ignore():
            user.save(update_fields=["attributes"])
        Event.new(EventAction.NEXT_ACTION_COMPLETED, flow_slug=slug).from_http(
            self.request, user=user
        )
        return self.executor.stage_ok()


def plan_next_action(request: HttpRequest, flow: Flow) -> FlowPlan:
    """Plan one next action and clear it after successful completion."""
    planner = FlowPlanner(flow)
    planner.use_cache = False
    planner.allow_empty_flows = True
    plan = planner.plan(request)
    plan.append_stage(in_memory_stage(NextActionDoneStageView, flow_slug=flow.slug))
    return plan


def pending_logout_allowed(request: HttpRequest) -> bool:
    """Allow a restricted session to log out, even when its action list is invalid."""
    path = request.path
    read_request = request.method in ("GET", "HEAD")
    if read_request and path in ("/flows/-/cancel/", "/flows/-/default/invalidation/"):
        return True
    if path.startswith(("/if/flow/", "/api/v3/flows/executor/")):
        slug = path.removeprefix("/if/flow/").removeprefix("/api/v3/flows/executor/").strip("/")
        method_allowed = read_request or (
            path.startswith("/api/v3/flows/executor/") and request.method == "POST"
        )
        return (
            method_allowed
            and Flow.objects.filter(slug=slug, designation=FlowDesignation.INVALIDATION).exists()
        )
    return False


def pending_path_allowed(request: HttpRequest, action_slug: str) -> bool:
    """Allow only the active action flow and its runtime dependencies."""
    path = request.path
    read_request = request.method in ("GET", "HEAD")
    if read_request and (
        path in PENDING_ALLOWED_READ_PATHS or path.startswith(PENDING_ALLOWED_READ_PREFIXES)
    ):
        return True
    if path == f"/if/flow/{action_slug}/" and read_request:
        return True
    if path == f"/api/v3/flows/executor/{action_slug}/" and request.method in ("GET", "POST"):
        return True
    # Duo enrollment polls this flow-authenticated endpoint while its stage is active.
    if (
        request.method == "POST"
        and path.startswith("/api/v3/stages/authenticator/duo/")
        and path.endswith("/enrollment_status/")
    ):
        return True
    return False


class PendingNextActionsMiddleware:
    """Restrict a newly logged-in session until its next actions are complete."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.block_pending_user(request)
        return response or self.get_response(request)

    def block_pending_user(self, request: HttpRequest) -> HttpResponse | None:
        """Return a response for a user who must complete next actions first,
        None when the request may proceed."""
        if not request.session.get(SESSION_KEY_PENDING_NEXT_ACTIONS):
            return None
        if not request.user.is_authenticated:
            request.session.pop(SESSION_KEY_PENDING_NEXT_ACTIONS, None)
            return None
        if pending_logout_allowed(request):
            return None
        user = request.user
        value = user.attributes.get(USER_ATTRIBUTE_NEXT_ACTIONS)
        if not value:
            request.session.pop(SESSION_KEY_PENDING_NEXT_ACTIONS, None)
            return None
        from authentik.flows.exceptions import FlowNonApplicableException

        try:
            flows = resolve_next_actions(value)
        except ValueError as exc:
            LOGGER.warning("Failed to resolve next actions", user=user.username, error=str(exc))
            return JsonResponse(
                {"detail": _("The required actions are invalid. Contact your administrator.")},
                status=403,
            )
        if pending_path_allowed(request, flows[0].slug):
            return None
        if "text/html" not in request.headers.get("Accept", ""):
            return JsonResponse(
                {"detail": _("Complete the required actions before continuing.")},
                status=403,
            )
        try:
            plan = plan_next_action(request, flows[0])
        except FlowNonApplicableException:
            LOGGER.warning(
                "Next action flow not applicable to user",
                user=user.username,
            )
            return JsonResponse(
                {"detail": _("The required actions are invalid. Contact your administrator.")},
                status=403,
            )
        # Send the user back to where they were once the actions are completed
        plan.context[PLAN_CONTEXT_REDIRECT] = request.get_full_path()
        request.session[SESSION_KEY_PLAN] = plan
        return redirect("authentik_core:if-flow", flow_slug=flows[0].slug)
