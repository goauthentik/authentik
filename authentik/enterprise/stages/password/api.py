"""Enterprise password lockout API extensions."""

from django.db import transaction
from django.utils.timezone import now
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import SERVICE_ACCOUNT_TYPES
from authentik.enterprise.api import enterprise_action
from authentik.events.models import Event, EventAction
from authentik.stages.password.models import PasswordDevice


class PasswordDeviceLockoutMixin:
    """Enterprise lock action for password authenticators."""

    @extend_schema(
        request=None,
        responses={204: OpenApiResponse(description="Successfully locked authenticator")},
    )
    @action(detail=True, methods=["POST"])
    @enterprise_action
    @transaction.atomic
    def lock(self, request: Request, pk: int) -> Response:
        """Prevent a password authenticator from authenticating."""
        device = self.get_object()
        if device.user.type in SERVICE_ACCOUNT_TYPES:
            raise ValidationError(
                {"non_field_errors": _("A service account's password cannot be locked.")}
            )
        if PasswordDevice.objects.filter(pk=device.pk, locked_at__isnull=True).update(
            failed_attempts=0, locked_at=now()
        ):
            Event.new(
                EventAction.AUTHENTICATOR_LOCKED,
                affected_user=device.user,
                authenticator=device,
                reason="administrator",
            ).from_http(request)
        return Response(status=204)
