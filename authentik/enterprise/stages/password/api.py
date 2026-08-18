"""Enterprise password lockout API extensions."""

from typing import Any

from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import User, UserTypes
from authentik.enterprise.api import enterprise_action
from authentik.enterprise.stages.password.lockout import (
    is_password_lockout_available,
    lock_password,
)
from authentik.rbac.decorators import permission_required
from authentik.stages.password.models import PasswordStage

LOCKOUT_FIELD_DEFAULTS = {
    "failed_attempts_before_lockout": 0,
    "show_last_attempt_warning": False,
    "last_attempt_warning_message": "",
    "show_lockout_message": False,
    "lockout_message": "",
}


class PasswordStageSerializerMixin:
    """Require Enterprise when password lockout settings change."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not is_password_lockout_available():
            instance = self.instance if isinstance(self.instance, PasswordStage) else None
            for field, default in LOCKOUT_FIELD_DEFAULTS.items():
                if field not in attrs:
                    continue
                current = getattr(instance, field, default)
                if attrs[field] not in (current, default):
                    raise ValidationError(
                        _("Enterprise is required to configure password lockout.")
                    )
        return super().validate(attrs)


class UserPasswordLockoutMixin:
    """Enterprise password lock action for UserViewSet."""

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        request=None,
        responses={204: OpenApiResponse(description="Successfully locked password")},
    )
    @action(detail=True, methods=["POST"])
    @enterprise_action
    def lock_password(self, request: Request, pk: int) -> Response:
        """Prevent a user's password from authenticating."""
        user: User = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError({"non_field_errors": _("You cannot lock your own password.")})
        if not user.is_active:
            raise ValidationError(
                {"non_field_errors": _("A deactivated user's password cannot be locked.")}
            )
        if user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            raise ValidationError(
                {"non_field_errors": _("A service account's password cannot be locked.")}
            )
        lock_password(user, request._request)
        return Response(status=204)
