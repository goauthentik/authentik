"""AuthenticatorEndpointStage API Views"""

from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_endpoint.models import (
    AuthenticatorEndpointStage,
    EndpointDevice,
)

LOGGER = get_logger()


class AuthenticatorEndpointStageSerializer(StageSerializer):
    """AuthenticatorEndpointStage Serializer"""

    class Meta:
        model = AuthenticatorEndpointStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
        ]


class AuthenticatorEndpointStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorEndpointStage Viewset"""

    queryset = AuthenticatorEndpointStage.objects.all()
    serializer_class = AuthenticatorEndpointStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
    ]
    search_fields = ["name"]
    ordering = ["name"]


class EndpointDeviceSerializer(ModelSerializer):
    """Serializer for Endpoint authenticator devices"""

    class Meta:
        model = EndpointDevice
        fields = ["pk", "name"]
        depth = 2


class EndpointDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for Endpoint authenticator devices"""

    queryset = EndpointDevice.objects.all()
    serializer_class = EndpointDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]


class EndpointAdminDeviceViewSet(ModelViewSet):
    """Viewset for Endpoint authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = EndpointDevice.objects.all()
    serializer_class = EndpointDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
