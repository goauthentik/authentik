"""Required action validation for users"""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from authentik.enterprise.required_actions import USER_ATTRIBUTE_REQUIRED_ACTIONS
from authentik.enterprise.required_actions.flows import resolve_required_actions


class RequiredActionsUserSerializerMixin:
    """Validate required actions on users"""

    def validate_attributes(self, attributes: dict) -> dict:
        """Reject required actions that cannot run"""
        key = USER_ATTRIBUTE_REQUIRED_ACTIONS
        current = self.instance.attributes if self.instance else {}
        # Only validate changes, so a flow deleted later doesn't block unrelated edits
        if key not in attributes or (key in current and attributes[key] == current[key]):
            return attributes
        try:
            resolve_required_actions(attributes[key])
        except ValueError as exc:
            raise ValidationError(
                _(
                    "Required actions must reference existing flows that a logged-in user "
                    "can run, other than authentication or invalidation flows."
                )
            ) from exc
        return attributes
