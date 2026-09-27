"""Next action flows required after login"""

from typing import Any

from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import USER_ATTRIBUTE_NEXT_ACTIONS, User
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.exceptions import FlowNonApplicableException
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


def next_actions_enabled() -> bool:
    """Enforce actions even when the installed license has expired."""
    from authentik.enterprise.license import LicenseKey
    from authentik.enterprise.models import LicenseUsageStatus

    return LicenseKey.cached_summary().status != LicenseUsageStatus.UNLICENSED


def next_action_slugs(value: Any) -> list[str]:
    """Normalize the next-actions attribute value to a list of slugs, without validation"""
    slugs = value if isinstance(value, list) else [value]
    return [slug for slug in slugs if isinstance(slug, str)]


def resolve_next_actions(value: Any) -> list[Flow]:
    """Resolve ordered flow slugs, rejecting missing or unusable flows."""
    slugs = value if isinstance(value, list) else [value]
    if any(not isinstance(slug, str) for slug in slugs):
        raise ValueError("Next actions must be flow slugs")
    flows = Flow.objects.exclude(designation__in=NEXT_ACTION_DISALLOWED_DESIGNATIONS).in_bulk(
        slugs, field_name="slug"
    )
    try:
        return [flows[slug] for slug in slugs]
    except KeyError as exc:
        raise ValueError("Next action flow is missing or has a disallowed designation") from exc


class NextActionDoneStageView(StageView):
    """Remove a completed next action flow from the user's attributes"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        slug = self.executor.current_stage.flow_slug
        with transaction.atomic(), audit_ignore():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            value = user.attributes.get(USER_ATTRIBUTE_NEXT_ACTIONS, [])
            actions = value if isinstance(value, list) else [value]
            if slug not in actions:
                return self.executor.stage_ok()
            actions.remove(slug)
            if actions:
                user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS] = actions
            else:
                user.attributes.pop(USER_ATTRIBUTE_NEXT_ACTIONS, None)
                request.session.pop(SESSION_KEY_PENDING_NEXT_ACTIONS, None)
            user.save(update_fields=["attributes"])
            Event.new(EventAction.NEXT_ACTION_COMPLETED, flow_slug=slug).from_http(
                request, user=user
            )
        return self.executor.stage_ok()


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
