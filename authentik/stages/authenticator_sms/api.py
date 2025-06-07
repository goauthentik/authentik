"""AuthenticatorSMSStage API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSDevice


class AuthenticatorSMSStageSerializer(StageSerializer):
    """AuthenticatorSMSStage Serializer"""

    class Meta:
        model = AuthenticatorSMSStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "provider",
            "from_number",
            "account_sid",
            "auth",
            "auth_password",
            "auth_type",
            "verify_only",
            "mapping",
        ]


class AuthenticatorSMSStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorSMSStage Viewset"""

    queryset = AuthenticatorSMSStage.objects.all()
    serializer_class = AuthenticatorSMSStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class SMSDeviceSerializer(ModelSerializer):
    """Serializer for sms authenticator devices"""

    user = GroupMemberSerializer(read_only=True)

    class Meta:
        model = SMSDevice
        fields = ["name", "pk", "phone_number", "user"]
        depth = 2
        extra_kwargs = {
            "phone_number": {"read_only": True},
        }


class SMSDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for sms authenticator devices"""

    queryset = SMSDevice.objects.all()
    serializer_class = SMSDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    owner_field = "user"


class SMSAdminDeviceViewSet(ModelViewSet):
    """Viewset for sms authenticator devices (for admins)"""

    queryset = SMSDevice.objects.all()
    serializer_class = SMSDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
