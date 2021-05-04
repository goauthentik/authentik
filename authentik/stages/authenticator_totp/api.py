"""AuthenticatorTOTPStage API Views"""
from django_otp.plugins.otp_totp.models import TOTPDevice
from guardian.utils import get_anonymous_user
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage


class AuthenticatorTOTPStageSerializer(StageSerializer):
    """AuthenticatorTOTPStage Serializer"""

    class Meta:

        model = AuthenticatorTOTPStage
        fields = StageSerializer.Meta.fields + ["configure_flow", "digits"]


class AuthenticatorTOTPStageViewSet(ModelViewSet):
    """AuthenticatorTOTPStage Viewset"""

    queryset = AuthenticatorTOTPStage.objects.all()
    serializer_class = AuthenticatorTOTPStageSerializer


class TOTPDeviceSerializer(ModelSerializer):
    """Serializer for totp authenticator devices"""

    class Meta:

        model = TOTPDevice
        fields = [
            "name",
            "pk",
        ]
        depth = 2


class TOTPDeviceViewSet(ModelViewSet):
    """Viewset for totp authenticator devices"""

    queryset = TOTPDevice.objects.none()
    serializer_class = TOTPDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        return TOTPDevice.objects.filter(user=user.pk)


class TOTPAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for totp authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = TOTPDevice.objects.all()
    serializer_class = TOTPDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
