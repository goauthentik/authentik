"""AuthenticateWebAuthnStage API Views"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
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


class WebAuthnDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for WebAuthn authenticator devices"""

    queryset = WebAuthnDevice.objects.all()
    serializer_class = WebAuthnDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]


class WebAuthnAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for WebAuthn authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = WebAuthnDevice.objects.all()
    serializer_class = WebAuthnDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
