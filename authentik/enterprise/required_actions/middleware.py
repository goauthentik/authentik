"""Hold sessions to their required actions"""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.middleware import SESSION_KEY_IMPERSONATE_USER
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import LicenseUsageStatus
from authentik.enterprise.required_actions import USER_ATTRIBUTE_REQUIRED_ACTIONS
from authentik.enterprise.required_actions.flows import (
    get_completion_stage,
    plan_required_action,
    resolve_required_actions,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowDesignation, Stage
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import (
    QS_QUERY,
    SESSION_KEY_PLAN,
    SESSION_KEY_POST,
    to_stage_response,
)
from authentik.lib.utils.urls import reverse_with_qs

LOGGER = get_logger()

# Routes a session with required actions can always use
ALLOWED_ROUTES = [
    # Read by the flow interface
    "authentik_api:config",
    "authentik_api:user-me",
    "authentik_flows:cancel",
    "authentik_flows:default-invalidation",
    # Duo enrollment polls this endpoint while its stage is active
    "authentik_api:authenticatorduostage-enrollment-status",
]
ROUTE_FLOW_INTERFACE = "authentik_core:if-flow"
ROUTE_FLOW_EXECUTOR = "authentik_api:flow-executor"


class RequiredActionsMiddleware(MiddlewareMixin):
    """Send a user through their required actions before they can do anything else.

    Whatever the user was doing is suspended: a flow in progress is stored with the action
    and restored once it is complete, any other page is revisited."""

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        user = request.user
        route = request.resolver_match.view_name
        if (
            not user.is_authenticated
            or user.attributes.get(USER_ATTRIBUTE_REQUIRED_ACTIONS, []) == []
            or route in ALLOWED_ROUTES
            # An administrator impersonating the user must not complete actions for them
            or SESSION_KEY_IMPERSONATE_USER in request.session
            # An expired license still enforces actions, so expiry cannot release a user
            or LicenseKey.cached_summary().status == LicenseUsageStatus.UNLICENSED
        ):
            return None
        flow = None
        if route in (ROUTE_FLOW_INTERFACE, ROUTE_FLOW_EXECUTOR):
            flow = Flow.objects.filter(slug=view_kwargs["flow_slug"]).first()
            if flow and flow.designation == FlowDesignation.INVALIDATION:
                return None
        try:
            action = resolve_required_actions(user.attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS])[0]
            return self.enforce(request, action, flow)
        except (ValueError, FlowNonApplicableException) as exc:
            LOGGER.warning("Invalid required action", user=user.username, error=str(exc))
            return JsonResponse(
                {"detail": _("The required actions are invalid. Contact your administrator.")},
                status=403,
            )

    def enforce(self, request: HttpRequest, action: Flow, flow: Flow | None) -> HttpResponse | None:
        """Let the request through only if it runs `action`, otherwise start `action`."""
        executor = request.resolver_match.view_name == ROUTE_FLOW_EXECUTOR
        plan: FlowPlan | None = request.session.get(SESSION_KEY_PLAN)
        completion = get_completion_stage(plan)
        running = completion is not None and completion.flow_slug == action.slug
        if flow == action:
            if executor and not running:
                self.start(request, action, flow, plan, completion)
            return None
        if not executor and "text/html" not in request.headers.get("Accept", ""):
            return JsonResponse(
                {"detail": _("Complete the required actions before continuing.")}, status=403
            )
        if not running:
            self.start(request, action, flow, plan, completion)
            messages.info(request, _("Complete the required actions before continuing."))
        response = redirect(ROUTE_FLOW_INTERFACE, flow_slug=action.slug)
        return to_stage_response(request, response) if executor else response

    def start(
        self,
        request: HttpRequest,
        action: Flow,
        flow: Flow | None,
        plan: FlowPlan | None,
        completion: Stage | None,
    ):
        """Plan `action`, suspending what the user requested."""
        if completion:
            # An earlier action was replaced before it was complete; keep what it suspended
            resume_url, resume_plan = completion.resume_url, completion.resume_plan
        elif flow == action:
            resume_url, resume_plan = reverse("authentik_core:root-redirect"), None
        else:
            if request.resolver_match.view_name == ROUTE_FLOW_EXECUTOR:
                resume_url = reverse_with_qs(
                    ROUTE_FLOW_INTERFACE,
                    QueryDict(request.GET.get(QS_QUERY, "")),
                    kwargs=request.resolver_match.kwargs,
                )
            else:
                resume_url = request.get_full_path()
                # The page is opened again with GET, so keep a POST body for it (mostly SAML)
                if request.method == "POST":
                    request.session[SESSION_KEY_POST] = request.POST
            in_progress = plan and flow and plan.flow_pk == flow.pk.hex
            resume_plan = plan if in_progress else None
        plan_required_action(request, action, resume_url, resume_plan)
