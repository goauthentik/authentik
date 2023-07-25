"""AuthenticatorMobileStage API Views"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.stages.authenticator_mobile.models import MobileDevice


class MobileDeviceSerializer(ModelSerializer):
    """Serializer for Mobile authenticator devices"""

    class Meta:
        model = MobileDevice
        fields = ["pk", "name"]
        depth = 2


class MobileDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for Mobile authenticator devices"""

    queryset = MobileDevice.objects.all()
    serializer_class = MobileDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]


class AdminMobileDeviceViewSet(ModelViewSet):
    """Viewset for Mobile authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = MobileDevice.objects.all()
    serializer_class = MobileDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
