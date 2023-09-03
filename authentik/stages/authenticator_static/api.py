"""AuthenticatorStaticStage API Views"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
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

    class Meta:
        model = StaticDevice
        fields = ["name", "token_set", "pk"]


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
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]


class StaticAdminDeviceViewSet(ModelViewSet):
    """Viewset for static authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = StaticDevice.objects.all()
    serializer_class = StaticDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
