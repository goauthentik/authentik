"""Enterprise password lockout API extensions."""

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils.timezone import now
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import User
from authentik.enterprise.api import enterprise_action
from authentik.events.models import Event, EventAction
from authentik.rbac.decorators import permission_required
from authentik.stages.password.lockout import SERVICE_ACCOUNT_TYPES
from authentik.stages.password.models import PasswordDevice


class UserPasswordLockoutMixin:
    """Enterprise password lock action for UserViewSet."""

    @permission_required("authentik_core.reset_user_password")
    @extend_schema(
        request=None,
        responses={204: OpenApiResponse(description="Successfully locked password")},
    )
    @action(detail=True, methods=["POST"], permission_classes=[IsAuthenticated])
    @enterprise_action
    def lock_password(self, request: Request, pk: int) -> Response:
        """Prevent a user's password from authenticating."""
        user: User = self.get_object()
        if user.type in SERVICE_ACCOUNT_TYPES:
            raise ValidationError(
                {"non_field_errors": _("A service account's password cannot be locked.")}
            )
        with transaction.atomic():
            PasswordDevice.objects.get_or_create(
                user=user, defaults={"name": "Password", "password": make_password(None)}
            )
            if PasswordDevice.objects.filter(user=user, locked_at__isnull=True).update(
                failed_attempts=0, locked_at=now()
            ):
                Event.new(
                    EventAction.PASSWORD_LOCKED, affected_user=user, reason="administrator"
                ).from_http(request)
        return Response(status=204)
