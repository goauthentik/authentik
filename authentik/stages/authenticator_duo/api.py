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
from structlog.stdlib import get_logger

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_duo.stage import SESSION_KEY_DUO_ENROLL
from authentik.stages.authenticator_duo.tasks import duo_import_devices

LOGGER = get_logger()


class AuthenticatorDuoStageSerializer(StageSerializer):
    """AuthenticatorDuoStage Serializer"""

    class Meta:
        model = AuthenticatorDuoStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "client_id",
            "client_secret",
            "api_hostname",
            "admin_integration_key",
            "admin_secret_key",
        ]
        extra_kwargs = {
            "client_secret": {"write_only": True},
            "admin_secret_key": {"write_only": True},
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
            200: inline_serializer(
                "DuoDeviceEnrollmentStatusSerializer",
                {
                    "duo_response": ChoiceField(
                        (
                            ("success", "Success"),
                            ("waiting", "Waiting"),
                            ("invalid", "Invalid"),
                        )
                    )
                },
            ),
        },
    )
    @action(methods=["POST"], detail=True, permission_classes=[])
    def enrollment_status(self, request: Request, pk: str) -> Response:
        """Check enrollment status of user details in current session"""
        stage: AuthenticatorDuoStage = AuthenticatorDuoStage.objects.filter(pk=pk).first()
        if not stage:
            raise Http404
        client = stage.auth_client()
        enroll = self.request.session.get(SESSION_KEY_DUO_ENROLL)
        if not enroll:
            return Response(status=400)
        status = client.enroll_status(enroll["user_id"], enroll["activation_code"])
        return Response({"duo_response": status})

    @permission_required(
        "", ["authentik_stages_authenticator_duo.add_duodevice", "authentik_core.view_user"]
    )
    @extend_schema(
        request=inline_serializer(
            "AuthenticatorDuoStageManualDeviceImport",
            {
                "duo_user_id": CharField(required=True),
                "username": CharField(required=True),
            },
        ),
        responses={
            204: OpenApiResponse(description="Enrollment successful"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(methods=["POST"], detail=True)
    def import_device_manual(self, request: Request, pk: str) -> Response:
        """Import duo devices into authentik"""
        stage: AuthenticatorDuoStage = self.get_object()
        user = (
            get_objects_for_user(request.user, "authentik_core.view_user")
            .filter(username=request.data.get("username", ""))
            .first()
        )
        if not user:
            return Response(data={"non_field_errors": ["User does not exist."]}, status=400)
        device = DuoDevice.objects.filter(
            duo_user_id=request.data.get("duo_user_id"), user=user, stage=stage
        ).first()
        if device:
            return Response(data={"non_field_errors": ["Device exists already."]}, status=400)
        DuoDevice.objects.create(
            duo_user_id=request.data.get("duo_user_id"),
            user=user,
            stage=stage,
            confirmed=True,
            name="Imported Duo Authenticator",
        )
        return Response(status=204)

    @permission_required(
        "", ["authentik_stages_authenticator_duo.add_duodevice", "authentik_core.view_user"]
    )
    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                "AuthenticatorDuoStageDeviceImportResponse",
                fields={
                    "count": IntegerField(read_only=True),
                    "error": CharField(read_only=True),
                },
            ),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(methods=["POST"], detail=True)
    def import_devices_automatic(self, request: Request, pk: str) -> Response:
        """Import duo devices into authentik"""
        stage: AuthenticatorDuoStage = self.get_object()
        if stage.admin_integration_key == "":
            return Response(
                data={
                    "non_field_errors": [
                        "Stage does not have Admin API configured, "
                        "which is required for automatic imports."
                    ]
                },
                status=400,
            )
        result = duo_import_devices.delay(str(stage.pk)).get()
        return Response(data=result, status=200 if result["error"] == "" else 400)


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
