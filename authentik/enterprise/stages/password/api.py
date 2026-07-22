"""Enterprise password stage API extensions."""

from typing import Any

from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import User, UserTypes
from authentik.enterprise.api import enterprise_action
from authentik.enterprise.license import LicenseKey
from authentik.enterprise.stages.password.lockout import (
    lock_password_login,
    unlock_password_login,
)
from authentik.rbac.decorators import permission_required

ENTERPRISE_FIELDS = (
    "failed_attempts_before_lockout",
    "show_last_attempt_warning",
    "last_attempt_warning_message",
    "show_lockout_message",
    "lockout_message",
)


class PasswordStageSerializerMixin:
    """Require Enterprise when password lockout settings are enabled."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        values = {
            field: attrs.get(field, getattr(self.instance, field, None))
            for field in ENTERPRISE_FIELDS
        }
        if any(values.values()) and not LicenseKey.cached_summary().status.is_valid:
            raise ValidationError(_("Enterprise is required to configure password lockout."))
        return super().validate(attrs)


class UserPasswordLoginMixin:
    """Enterprise password-login actions for UserViewSet."""

    conditional_select_related = ("password_login_state",)

    @permission_required("authentik_core.change_user")
    @extend_schema(
        request=None,
        responses={204: OpenApiResponse(description="Password login locked")},
    )
    @action(detail=True, methods=["POST"])
    @enterprise_action
    def password_login_lock(self, request: Request, pk: int) -> Response:
        """Lock password login for a user."""
        user: User = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError(
                {"non_field_errors": _("You cannot lock password login for your own account.")}
            )
        if not user.is_active:
            raise ValidationError(
                {"non_field_errors": _("Password login cannot be locked for a deactivated user.")}
            )
        if user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            raise ValidationError(
                {
                    "non_field_errors": _(
                        "Password login cannot be locked for an internal service account."
                    )
                }
            )
        lock_password_login(user, request._request, reason="administrator")
        return Response(status=204)

    @permission_required("authentik_core.change_user")
    @extend_schema(
        request=None,
        responses={204: OpenApiResponse(description="Password login unlocked")},
    )
    @action(detail=True, methods=["POST"])
    @enterprise_action
    def password_login_unlock(self, request: Request, pk: int) -> Response:
        """Unlock password login for a user."""
        user: User = self.get_object()
        unlock_password_login(user, request._request, reason="administrator")
        return Response(status=204)
