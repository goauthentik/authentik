"""AuthenticatorSMSStage API Views"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSDevice


class AuthenticatorSMSStageSerializer(StageSerializer):
    """AuthenticatorSMSStage Serializer"""

    class Meta:

        model = AuthenticatorSMSStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "provider",
            "from_number",
            "account_sid",
            "auth",
            "auth_password",
            "auth_type",
            "verify_only",
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

    class Meta:

        model = SMSDevice
        fields = ["name", "pk", "phone_number"]
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
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]


class SMSAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for sms authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = SMSDevice.objects.all()
    serializer_class = SMSDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
