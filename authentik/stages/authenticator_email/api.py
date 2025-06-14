"""AuthenticatorEmailStage API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage, EmailDevice


class AuthenticatorEmailStageSerializer(StageSerializer):
    """AuthenticatorEmailStage Serializer"""

    class Meta:
        model = AuthenticatorEmailStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "use_global_settings",
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
            "from_address",
            "subject",
            "token_expiry",
            "template",
        ]


class AuthenticatorEmailStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorEmailStage Viewset"""

    queryset = AuthenticatorEmailStage.objects.all()
    serializer_class = AuthenticatorEmailStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class EmailDeviceSerializer(ModelSerializer):
    """Serializer for email authenticator devices"""

    user = GroupMemberSerializer(read_only=True)

    class Meta:
        model = EmailDevice
        fields = ["name", "pk", "email", "user"]
        depth = 2
        extra_kwargs = {
            "email": {"read_only": True},
        }


class EmailDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for email authenticator devices"""

    queryset = EmailDevice.objects.all()
    serializer_class = EmailDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    owner_field = "user"


class EmailAdminDeviceViewSet(ModelViewSet):
    """Viewset for email authenticator devices (for admins)"""

    queryset = EmailDevice.objects.all()
    serializer_class = EmailDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
