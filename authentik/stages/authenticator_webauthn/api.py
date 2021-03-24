"""AuthenticateWebAuthnStage API Views"""
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_webauthn.models import (
    AuthenticateWebAuthnStage,
    WebAuthnDevice,
)


class AuthenticateWebAuthnStageSerializer(StageSerializer):
    """AuthenticateWebAuthnStage Serializer"""

    class Meta:

        model = AuthenticateWebAuthnStage
        fields = StageSerializer.Meta.fields + ["configure_flow"]


class AuthenticateWebAuthnStageViewSet(ModelViewSet):
    """AuthenticateWebAuthnStage Viewset"""

    queryset = AuthenticateWebAuthnStage.objects.all()
    serializer_class = AuthenticateWebAuthnStageSerializer


class WebAuthnDeviceSerializer(ModelSerializer):
    """Serializer for WebAuthn authenticator devices"""

    class Meta:

        model = WebAuthnDevice
        fields = ["pk", "name", "created_on"]
        depth = 2


class WebAuthnDeviceViewSet(ModelViewSet):
    """Viewset for WebAuthn authenticator devices"""

    queryset = WebAuthnDevice.objects.none()
    serializer_class = WebAuthnDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        if not self.request:
            return super().get_queryset()
        return WebAuthnDevice.objects.filter(user=self.request.user)


class WebAuthnAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for WebAuthn authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = WebAuthnDevice.objects.all()
    serializer_class = WebAuthnDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
