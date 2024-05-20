"""AuthenticatorWebAuthnStage API Views"""

from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.stages.authenticator_webauthn.api.device_types import WebAuthnDeviceTypeSerializer
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice


class WebAuthnDeviceSerializer(ModelSerializer):
    """Serializer for WebAuthn authenticator devices"""

    device_type = WebAuthnDeviceTypeSerializer(read_only=True, allow_null=True)

    class Meta:
        model = WebAuthnDevice
        fields = ["pk", "name", "created_on", "device_type", "aaguid"]
        extra_kwargs = {
            "aaguid": {"read_only": True},
        }


class WebAuthnDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
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


class WebAuthnAdminDeviceViewSet(ModelViewSet):
    """Viewset for WebAuthn authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = WebAuthnDevice.objects.all()
    serializer_class = WebAuthnDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
