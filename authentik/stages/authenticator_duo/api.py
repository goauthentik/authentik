"""AuthenticatorDuoStage API Views"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_duo.stage import (
    SESSION_KEY_DUO_ACTIVATION_CODE,
    SESSION_KEY_DUO_USER_ID,
)


class AuthenticatorDuoStageSerializer(StageSerializer):
    """AuthenticatorDuoStage Serializer"""

    class Meta:

        model = AuthenticatorDuoStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "client_id",
            "client_secret",
            "api_hostname",
        ]
        extra_kwargs = {
            "client_secret": {"write_only": True},
        }


class AuthenticatorDuoStageViewSet(ModelViewSet):
    """AuthenticatorDuoStage Viewset"""

    queryset = AuthenticatorDuoStage.objects.all()
    serializer_class = AuthenticatorDuoStageSerializer

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Enrollment successful"),
            420: OpenApiResponse(description="Enrollment pending/failed"),
        },
    )
    @action(methods=["POST"], detail=True, permission_classes=[])
    # pylint: disable=invalid-name,unused-argument
    def enrollment_status(self, request: Request, pk: str) -> Response:
        """Check enrollment status of user details in current session"""
        stage: AuthenticatorDuoStage = self.get_object()
        client = stage.client
        user_id = self.request.session.get(SESSION_KEY_DUO_USER_ID)
        activation_code = self.request.session.get(SESSION_KEY_DUO_ACTIVATION_CODE)
        status = client.enroll_status(user_id, activation_code)
        if status == "success":
            return Response(status=204)
        return Response(status=420)


class DuoDeviceSerializer(ModelSerializer):
    """Serializer for Duo authenticator devices"""

    class Meta:

        model = DuoDevice
        fields = ["pk", "name"]
        depth = 2


class DuoDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for Duo authenticator devices"""

    queryset = DuoDevice.objects.all()
    serializer_class = DuoDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]


class DuoAdminDeviceViewSet(ReadOnlyModelViewSet):
    """Viewset for Duo authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = DuoDevice.objects.all()
    serializer_class = DuoDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
