"""AuthenticatorStaticStage API Views"""
from django_filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_otp.plugins.otp_static.models import StaticDevice
from guardian.utils import get_anonymous_user
from rest_framework.filters import SearchFilter
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
        fields = ["name", "token_set", "pk"]
        depth = 2


class StaticDeviceViewSet(ModelViewSet):
    """Viewset for static authenticator devices"""

    queryset = StaticDevice.objects.none()
    serializer_class = StaticDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        return StaticDevice.objects.filter(user=user.pk)


class StaticAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for static authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = StaticDevice.objects.all()
    serializer_class = StaticDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
