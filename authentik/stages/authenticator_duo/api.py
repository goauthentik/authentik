"""AuthenticatorDuoStage API Views"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework import mixins
from rest_framework.decorators import action
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


class AuthenticatorDuoStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorDuoStage Viewset"""

    queryset = AuthenticatorDuoStage.objects.all()
    serializer_class = AuthenticatorDuoStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
        "client_id",
        "api_hostname",
    ]
    search_fields = ["name"]
    ordering = ["name"]

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
        if not user_id or not activation_code:
            return Response(status=420)
        status = client.enroll_status(user_id, activation_code)
        if status == "success":
            return Response(status=204)
        return Response(status=420)

    @permission_required(
        "", ["authentik_stages_authenticator_duo.add_duodevice", "authentik_core.view_user"]
    )
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="duo_user_id", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name="username", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY
            ),
        ],
        responses={
            204: OpenApiResponse(description="Enrollment successful"),
            400: OpenApiResponse(description="Device exists already"),
        },
    )
    @action(methods=["POST"], detail=True)
    # pylint: disable=invalid-name,unused-argument
    def import_devices(self, request: Request, pk: str) -> Response:
        """Import duo devices into authentik"""
        stage: AuthenticatorDuoStage = self.get_object()
        user = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(username=request.query_params.get("username", ""))
            .first()
        )
        if not user:
            return Response(data={"non_field_errors": ["user does not exist"]}, status=400)
        device = DuoDevice.objects.filter(
            duo_user_id=request.query_params.get("duo_user_id"), user=user, stage=stage
        ).first()
        if device:
            return Response(data={"non_field_errors": ["device exists already"]}, status=400)
        DuoDevice.objects.create(
            duo_user_id=request.query_params.get("duo_user_id"), user=user, stage=stage
        )
        return Response(status=204)


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
    UsedByMixin,
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


class DuoAdminDeviceViewSet(ModelViewSet):
    """Viewset for Duo authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = DuoDevice.objects.all()
    serializer_class = DuoDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
