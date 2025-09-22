"""AuthenticatorStaticStage API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.groups import GroupMemberSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_static.models import (
    AuthenticatorStaticStage,
    StaticDevice,
    StaticToken,
)


class AuthenticatorStaticStageSerializer(StageSerializer):
    """AuthenticatorStaticStage Serializer"""

    class Meta:
        model = AuthenticatorStaticStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "token_count",
            "token_length",
        ]


class AuthenticatorStaticStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorStaticStage Viewset"""

    queryset = AuthenticatorStaticStage.objects.all()
    serializer_class = AuthenticatorStaticStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class StaticDeviceTokenSerializer(ModelSerializer):
    """Serializer for static device's tokens"""

    class Meta:
        model = StaticToken
        fields = ["token"]


class StaticDeviceSerializer(ModelSerializer):
    """Serializer for static authenticator devices"""

    token_set = StaticDeviceTokenSerializer(many=True, read_only=True)
    user = GroupMemberSerializer(read_only=True)

    class Meta:
        model = StaticDevice
        fields = ["name", "token_set", "pk", "user"]


class StaticDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for static authenticator devices"""

    queryset = StaticDevice.objects.filter(confirmed=True)
    serializer_class = StaticDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    owner_field = "user"


class StaticAdminDeviceViewSet(ModelViewSet):
    """Viewset for static authenticator devices (for admins)"""

    queryset = StaticDevice.objects.all()
    serializer_class = StaticDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
