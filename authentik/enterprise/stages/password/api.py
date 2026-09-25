"""Enterprise password lockout API extensions."""

from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from authentik.core.models import User
from authentik.enterprise.api import enterprise_action
from authentik.enterprise.stages.password.lockout import SERVICE_ACCOUNT_TYPES, PasswordLockout
from authentik.rbac.decorators import permission_required


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
        if user.type in SERVICE_ACCOUNT_TYPES:
            raise ValidationError(
                {"non_field_errors": _("A service account's password cannot be locked.")}
            )
        PasswordLockout.lock(user, request._request)
        return Response(status=204)
