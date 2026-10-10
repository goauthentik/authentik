"""Required action flows"""

from typing import Any

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from authentik.core.models import User
from authentik.enterprise.required_actions import USER_ATTRIBUTE_REQUIRED_ACTIONS
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, FlowDesignation, Stage, in_memory_stage
from authentik.flows.planner import FlowPlan, FlowPlanner
from authentik.flows.stage import StageView
from authentik.flows.views.executor import SESSION_KEY_PLAN

# Flows that create or end a session cannot run as a required action
DISALLOWED_DESIGNATIONS = [FlowDesignation.AUTHENTICATION, FlowDesignation.INVALIDATION]


def resolve_required_actions(value: Any) -> list[Flow]:
    """Resolve ordered flow slugs, rejecting missing or unusable flows."""
    slugs = value if isinstance(value, list) else [value]
    if any(not isinstance(slug, str) for slug in slugs):
        raise ValueError("Required actions must be flow slugs")
    flows = Flow.objects.exclude(designation__in=DISALLOWED_DESIGNATIONS).in_bulk(
        slugs, field_name="slug"
    )
    try:
        return [flows[slug] for slug in slugs]
    except KeyError as exc:
        raise ValueError("Required action flow is missing or has a disallowed designation") from exc


def plan_required_action(
    request: HttpRequest, action: Flow, resume_url: str, resume_plan: FlowPlan | None
):
    """Start `action`, suspending what the user was doing until it is complete.

    `resume_url` is where the user goes afterwards; `resume_plan` is the flow they were
    in, if any, and is restored before redirecting there."""
    planner = FlowPlanner(action)
    planner.use_cache = False
    planner.allow_empty_flows = True
    plan = planner.plan(request)
    plan.append_stage(
        in_memory_stage(
            RequiredActionCompleteStageView,
            flow_slug=action.slug,
            resume_url=resume_url,
            resume_plan=resume_plan,
        )
    )
    request.session[SESSION_KEY_PLAN] = plan


def get_completion_stage(plan: FlowPlan | None) -> Stage | None:
    """Find the completion stage of a required action plan."""
    if not plan:
        return None
    for binding in plan.bindings:
        if binding.stage.view is RequiredActionCompleteStageView:
            return binding.stage
    return None


class RequiredActionCompleteStageView(StageView):
    """Remove the completed action from the user, then resume what they were doing"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        stage = self.executor.current_stage
        # The completion event replaces the user update event
        with transaction.atomic(), audit_ignore():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            value = user.attributes.get(USER_ATTRIBUTE_REQUIRED_ACTIONS, [])
            actions = value if isinstance(value, list) else [value]
            if stage.flow_slug in actions:
                actions.remove(stage.flow_slug)
                if actions:
                    user.attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS] = actions
                else:
                    del user.attributes[USER_ATTRIBUTE_REQUIRED_ACTIONS]
                user.save(update_fields=["attributes"])
                Event.new(
                    EventAction.REQUIRED_ACTION_COMPLETED, flow_slug=stage.flow_slug
                ).from_http(request, user=user)
        self.executor.cancel()
        if stage.resume_plan:
            request.session[SESSION_KEY_PLAN] = stage.resume_plan
        return redirect(stage.resume_url)
