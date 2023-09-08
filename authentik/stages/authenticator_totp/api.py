"""AuthenticatorTOTPStage API Views"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage, TOTPDevice


class AuthenticatorTOTPStageSerializer(StageSerializer):
    """AuthenticatorTOTPStage Serializer"""

    class Meta:
        model = AuthenticatorTOTPStage
        fields = StageSerializer.Meta.fields + ["configure_flow", "friendly_name", "digits"]


class AuthenticatorTOTPStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorTOTPStage Viewset"""

    queryset = AuthenticatorTOTPStage.objects.all()
    serializer_class = AuthenticatorTOTPStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class TOTPDeviceSerializer(ModelSerializer):
    """Serializer for totp authenticator devices"""

    class Meta:
        model = TOTPDevice
        fields = [
            "name",
            "pk",
        ]
        depth = 2


class TOTPDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for totp authenticator devices"""

    queryset = TOTPDevice.objects.filter(confirmed=True)
    serializer_class = TOTPDeviceSerializer
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]


class TOTPAdminDeviceViewSet(ModelViewSet):
    """Viewset for totp authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = TOTPDevice.objects.all()
    serializer_class = TOTPDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
