"""AuthenticateWebAuthnStage API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_webauthn.api.device_types import WebAuthnDeviceTypeSerializer
from authentik.stages.authenticator_webauthn.models import AuthenticateWebAuthnStage


class AuthenticateWebAuthnStageSerializer(StageSerializer):
    """AuthenticateWebAuthnStage Serializer"""

    device_type_restrictions_obj = WebAuthnDeviceTypeSerializer(
        source="device_type_restrictions", many=True, read_only=True
    )

    class Meta:
        model = AuthenticateWebAuthnStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "user_verification",
            "authenticator_attachment",
            "resident_key_requirement",
            "device_type_restrictions",
            "device_type_restrictions_obj",
        ]


class AuthenticateWebAuthnStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticateWebAuthnStage Viewset"""

    queryset = AuthenticateWebAuthnStage.objects.all()
    serializer_class = AuthenticateWebAuthnStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]
