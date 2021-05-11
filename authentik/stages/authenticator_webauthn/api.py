"""AuthenticateWebAuthnStage API Views"""
from django_filters.rest_framework import DjangoFilterBackend
from guardian.utils import get_anonymous_user
from rest_framework.filters import OrderingFilter, SearchFilter
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
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        return WebAuthnDevice.objects.filter(user=user.pk)


class WebAuthnAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for WebAuthn authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = WebAuthnDevice.objects.all()
    serializer_class = WebAuthnDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
