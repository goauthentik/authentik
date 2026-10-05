"""PasswordStage API Views"""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.flows.api.stages import StageSerializer
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.rbac.filters import ObjectFilter
from authentik.stages.password.models import PasswordDevice, PasswordStage


class PasswordStageSerializer(StageSerializer):
    """PasswordStage Serializer"""

    class Meta:
        model = PasswordStage
        fields = StageSerializer.Meta.fields + [
            "backends",
            "configure_flow",
            "failed_attempts_before_cancel",
            "failed_attempts_before_lockout",
            "last_attempt_warning_message",
            "lockout_message",
            "allow_show_password",
        ]


class PasswordStageViewSet(UsedByMixin, ModelViewSet):
    """PasswordStage Viewset"""

    queryset = PasswordStage.objects.all()
    serializer_class = PasswordStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
        "failed_attempts_before_cancel",
        "failed_attempts_before_lockout",
        "allow_show_password",
    ]
    search_fields = ["name"]
    ordering = ["name"]


class PasswordDeviceViewSet(
    ConditionalInheritance("authentik.enterprise.stages.password.api.PasswordDeviceLockoutMixin"),
    GenericViewSet,
):
    """Manage password locks with the owning user's password-reset permission."""

    queryset = PasswordDevice.objects.select_related("user")
    permission_classes = [IsAuthenticated]
    filter_backends = []

    def get_queryset(self):
        users = ObjectFilter().filter_queryset(self.request, User.objects.all(), self)
        return super().get_queryset().filter(user__in=users)

    def get_object(self) -> PasswordDevice:
        device = super().get_object()
        permission = "authentik_core.reset_user_password"
        if not (
            self.request.user.has_perm(permission)
            or self.request.user.has_perm(permission, device.user)
        ):
            self.permission_denied(self.request)
        return device

    @extend_schema(
        request=None,
        responses={204: OpenApiResponse(description="Successfully unlocked authenticator")},
    )
    @action(detail=True, methods=["POST"])
    def unlock(self, request: Request, pk: int) -> Response:
        """Allow a locked password authenticator to authenticate again."""
        device = self.get_object()
        if PasswordDevice.objects.filter(pk=device.pk, locked_at__isnull=False).update(
            failed_attempts=0, locked_at=None
        ):
            Event.new(
                EventAction.AUTHENTICATOR_UNLOCKED,
                affected_user=device.user,
                authenticator=device,
            ).from_http(request)
        return Response(status=204)
