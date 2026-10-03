"""Restrict sessions while required actions remain."""

from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.enterprise.next_actions import USER_ATTRIBUTE_NEXT_ACTIONS
from authentik.enterprise.next_actions.flows import (
    SESSION_KEY_PENDING_NEXT_ACTIONS,
    NextActionDoneStageView,
    resolve_next_actions,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowDesignation, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_REDIRECT, FlowPlan, FlowPlanner
from authentik.flows.views.executor import SESSION_KEY_PLAN

LOGGER = get_logger()


def plan_next_action(request: HttpRequest, flow: Flow) -> FlowPlan:
    """Plan one next action and clear it after successful completion."""
    plan = request.session.get(SESSION_KEY_PLAN)
    if not plan or plan.flow_pk != flow.pk.hex:
        planner = FlowPlanner(flow)
        planner.use_cache = False
        planner.allow_empty_flows = True
        plan = planner.plan(request)
    if not any(binding.stage.view is NextActionDoneStageView for binding in plan.bindings):
        plan.append_stage(in_memory_stage(NextActionDoneStageView, flow_slug=flow.slug))
    return plan


class PendingNextActionsMiddleware(MiddlewareMixin):
    """Restrict a new session until its required actions are complete."""

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        if not request.session.get(SESSION_KEY_PENDING_NEXT_ACTIONS):
            return None
        if not request.user.is_authenticated:
            request.session.pop(SESSION_KEY_PENDING_NEXT_ACTIONS, None)
            return None
        route = request.resolver_match.view_name
        read = request.method in ("GET", "HEAD")
        flow_request = (read and route == "authentik_core:if-flow") or (
            request.method in ("GET", "POST") and route == "authentik_api:flow-executor"
        )
        slug = view_kwargs.get("flow_slug")
        if (
            read and route in ("authentik_flows:cancel", "authentik_flows:default-invalidation")
        ) or (
            flow_request
            and Flow.objects.filter(slug=slug, designation=FlowDesignation.INVALIDATION).exists()
        ):
            return None
        user = request.user
        value = user.attributes.get(USER_ATTRIBUTE_NEXT_ACTIONS, [])
        if value == []:
            request.session.pop(SESSION_KEY_PENDING_NEXT_ACTIONS, None)
            return None
        try:
            flow = resolve_next_actions(value)[0]
            plan = request.session.get(SESSION_KEY_PLAN)
            if plan and any(
                binding.stage.view is NextActionDoneStageView
                and binding.stage.flow_slug == flow.slug
                for binding in plan.bindings
            ):
                flow = Flow.objects.get(pk=plan.flow_pk)
            if read and route in ("authentik_api:user-me", "authentik_api:config"):
                return None
            # Duo enrollment polls this endpoint while its stage is active.
            if (
                request.method == "POST"
                and route == "authentik_api:authenticatorduostage-enrollment-status"
            ):
                return None
            allowed = flow_request and slug == flow.slug
            if not allowed and "text/html" not in request.headers.get("Accept", ""):
                return JsonResponse(
                    {"detail": _("Complete the required actions before continuing.")}, status=403
                )
            plan = plan_next_action(request, flow)
        except (ValueError, FlowNonApplicableException, Flow.DoesNotExist) as exc:
            LOGGER.warning("Invalid required action", user=user.username, error=str(exc))
            return JsonResponse(
                {"detail": _("The required actions are invalid. Contact your administrator.")},
                status=403,
            )
        plan.context.setdefault(
            PLAN_CONTEXT_REDIRECT,
            reverse("authentik_core:root-redirect") if allowed else request.get_full_path(),
        )
        request.session[SESSION_KEY_PLAN] = plan
        if allowed:
            return None
        return redirect("authentik_core:if-flow", flow_slug=flow.slug)
