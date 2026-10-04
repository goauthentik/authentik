"""Required-action validation and audit events for users."""

from contextlib import nullcontext

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from authentik.core.models import User
from authentik.enterprise.next_actions import USER_ATTRIBUTE_NEXT_ACTIONS
from authentik.enterprise.next_actions.flows import resolve_next_actions
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction


def _action_slugs(user: User) -> set[str]:
    """Collect flow slugs for auditing, including when repairing malformed attributes."""
    value = user.attributes.get(USER_ATTRIBUTE_NEXT_ACTIONS)
    values = value if isinstance(value, list) else [value]
    return {slug for slug in values if isinstance(slug, str)}


class NextActionsUserSerializerMixin:
    """Validate and audit changes to required actions."""

    def create(self, validated_data: dict) -> User:
        instance = super().create(validated_data)
        self._log_next_action_changes(set(), instance)
        return instance

    def update(self, instance: User, validated_data: dict) -> User:
        previous_actions = _action_slugs(instance)
        actions_only = validated_data.keys() == {"attributes"} and (
            instance.attributes | {USER_ATTRIBUTE_NEXT_ACTIONS: None}
            == validated_data["attributes"] | {USER_ATTRIBUTE_NEXT_ACTIONS: None}
        )
        with audit_ignore() if actions_only else nullcontext():
            instance = super().update(instance, validated_data)
        self._log_next_action_changes(previous_actions, instance)
        return instance

    def _log_next_action_changes(self, previous_actions: set[str], instance: User):
        """Create events for next actions added to or removed from the user."""
        current_actions = _action_slugs(instance)
        request = self.context.get("request")
        changes = (
            (EventAction.NEXT_ACTION_SET, current_actions - previous_actions),
            (EventAction.NEXT_ACTION_REMOVED, previous_actions - current_actions),
        )
        for event_action, slugs in changes:
            for slug in sorted(slugs):
                # `username` in the context makes the event visible on the user's events tab
                event = Event.new(event_action, flow_slug=slug, username=instance.username)
                if request:
                    event.from_http(request)
                else:
                    event.save()

    def validate_attributes(self, attributes: dict) -> dict:
        """Validate that the next-actions attribute only holds usable flows."""
        if USER_ATTRIBUTE_NEXT_ACTIONS in attributes:
            try:
                resolve_next_actions(attributes[USER_ATTRIBUTE_NEXT_ACTIONS])
            except ValueError as exc:
                raise ValidationError(
                    _(
                        "Next actions must reference existing flows other than "
                        "authentication or invalidation flows."
                    )
                ) from exc
        return attributes
