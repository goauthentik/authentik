"""AuthenticatorStaticStage API Views"""
from django_otp.plugins.otp_static.models import StaticDevice
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_static.models import AuthenticatorStaticStage


class AuthenticatorStaticStageSerializer(StageSerializer):
    """AuthenticatorStaticStage Serializer"""

    class Meta:

        model = AuthenticatorStaticStage
        fields = StageSerializer.Meta.fields + ["configure_flow", "token_count"]


class AuthenticatorStaticStageViewSet(ModelViewSet):
    """AuthenticatorStaticStage Viewset"""

    queryset = AuthenticatorStaticStage.objects.all()
    serializer_class = AuthenticatorStaticStageSerializer


class StaticDeviceSerializer(ModelSerializer):
    """Serializer for static authenticator devices"""

    class Meta:

        model = StaticDevice
        fields = ["name", "token_set"]
        depth = 2


class StaticDeviceViewSet(ModelViewSet):
    """Viewset for static authenticator devices"""

    queryset = StaticDevice.objects.none()
    serializer_class = StaticDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        if not self.request:
            return super().get_queryset()
        return StaticDevice.objects.filter(user=self.request.user)


class StaticAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for static authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = StaticDevice.objects.all()
    serializer_class = StaticDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
