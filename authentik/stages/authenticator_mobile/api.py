"""AuthenticatorDuoStage API Views"""
from django.http import Http404
from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from guardian.shortcuts import get_objects_for_user
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import CharField, ChoiceField, IntegerField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_mobile.models import AuthenticatorMobileStage, MobileDevice


class AuthenticatorMobileStageSerializer(StageSerializer):
    """AuthenticatorMobileStage Serializer"""

    class Meta:
        model = AuthenticatorMobileStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
        ]
        # extra_kwargs = {
        #     "client_secret": {"write_only": True},
        #     "admin_secret_key": {"write_only": True},
        # }


class AuthenticatorMobileStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorMobileStage Viewset"""

    queryset = AuthenticatorMobileStage.objects.all()
    serializer_class = AuthenticatorMobileStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
    ]
    search_fields = ["name"]
    ordering = ["name"]

    @action(methods=["GET"], detail=True)
    def enrollment_callback(self, request: Request, pk: str) -> Response:
        pass


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
