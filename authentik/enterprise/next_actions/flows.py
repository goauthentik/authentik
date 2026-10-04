"""Next action flows required after login"""

from typing import Any

from django.db import transaction
from django.http import HttpRequest, HttpResponse

from authentik.core.models import User
from authentik.enterprise.next_actions import USER_ATTRIBUTE_NEXT_ACTIONS
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.stage import StageView

SESSION_KEY_PENDING_NEXT_ACTIONS = "authentik/stages/user_login/pending_next_actions"

# Flows that create or end a session cannot run as a next action
NEXT_ACTION_DISALLOWED_DESIGNATIONS = [
    FlowDesignation.AUTHENTICATION,
    FlowDesignation.INVALIDATION,
]


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
