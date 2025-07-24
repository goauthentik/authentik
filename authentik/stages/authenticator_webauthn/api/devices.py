"""AuthenticatorWebAuthnStage API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.stages.authenticator_webauthn.api.device_types import WebAuthnDeviceTypeSerializer
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice


class WebAuthnDeviceSerializer(ModelSerializer):
    """Serializer for WebAuthn authenticator devices"""

    device_type = WebAuthnDeviceTypeSerializer(read_only=True, allow_null=True)
    user = GroupMemberSerializer(read_only=True)

    class Meta:
        model = WebAuthnDevice
        fields = ["pk", "name", "created_on", "device_type", "aaguid", "user"]
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
    owner_field = "user"


class WebAuthnAdminDeviceViewSet(ModelViewSet):
    """Viewset for WebAuthn authenticator devices (for admins)"""

    queryset = WebAuthnDevice.objects.all()
    serializer_class = WebAuthnDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
