"""AuthenticatorTOTPStage API Views"""

from rest_framework import mixins
from rest_framework.fields import ChoiceField
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_totp.models import (
    AuthenticatorTOTPStage,
    TOTPDevice,
    TOTPDigits,
)


class AuthenticatorTOTPStageSerializer(StageSerializer):
    """AuthenticatorTOTPStage Serializer"""

    digits = ChoiceField(choices=TOTPDigits.choices)

    class Meta:
        model = AuthenticatorTOTPStage
        fields = StageSerializer.Meta.fields + ["configure_flow", "friendly_name", "digits"]


class AuthenticatorTOTPStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorTOTPStage Viewset"""

    queryset = AuthenticatorTOTPStage.objects.all()
    serializer_class = AuthenticatorTOTPStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class TOTPDeviceSerializer(ModelSerializer):
    """Serializer for totp authenticator devices"""

    user = GroupMemberSerializer(read_only=True)

    class Meta:
        model = TOTPDevice
        fields = [
            "name",
            "pk",
            "user",
        ]
        depth = 2


class TOTPDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for totp authenticator devices"""

    queryset = TOTPDevice.objects.filter(confirmed=True)
    serializer_class = TOTPDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    owner_field = "user"


class TOTPAdminDeviceViewSet(ModelViewSet):
    """Viewset for totp authenticator devices (for admins)"""

    queryset = TOTPDevice.objects.all()
    serializer_class = TOTPDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
