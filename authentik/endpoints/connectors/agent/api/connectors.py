from typing import cast

from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import (
    CharField,
    ChoiceField,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.connectors.agent.api.agent import (
    AgentConfigSerializer,
    AgentTokenResponseSerializer,
    EnrollSerializer,
)
from authentik.endpoints.connectors.agent.auth import (
    AgentAuth,
    AgentEnrollmentAuth,
)
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    DeviceToken,
    EnrollmentToken,
)
from authentik.endpoints.facts import DeviceFacts, OSFamily
from authentik.endpoints.models import Device
from authentik.lib.utils.reflection import ConditionalInheritance


class AgentConnectorSerializer(ConnectorSerializer):

    class Meta(ConnectorSerializer.Meta):
        model = AgentConnector
        fields = ConnectorSerializer.Meta.fields + [
            "snapshot_expiry",
            "auth_terminate_session_on_expiry",
            "refresh_interval",
            "authorization_flow",
            "nss_uid_offset",
            "nss_gid_offset",
            "challenge_key",
            "jwt_federation_providers",
        ]


class MDMConfigSerializer(PassiveSerializer):

    platform = ChoiceField(choices=OSFamily.choices)
    enrollment_token = PrimaryKeyRelatedField(queryset=EnrollmentToken.objects.all())

    def validate_platform(self, platform: OSFamily) -> OSFamily:
        if platform not in [OSFamily.iOS, OSFamily.macOS, OSFamily.windows]:
            raise ValidationError(_("Selected platform not supported"))
        return platform

    def validate_enrollment_token(self, token: EnrollmentToken) -> EnrollmentToken:
        if token.is_expired:
            raise ValidationError(_("Token is expired"))
        if token.connector != self.context["connector"]:
            raise ValidationError(_("Invalid token for connector"))
        return token


class MDMConfigResponseSerializer(PassiveSerializer):

    config = CharField(required=True)


class AgentConnectorViewSet(
    ConditionalInheritance(
        "authentik.enterprise.endpoints.connectors.agent.api.connectors.AgentConnectorViewSetMixin"
    ),
    UsedByMixin,
    ModelViewSet,
):

    queryset = AgentConnector.objects.all()
    serializer_class = AgentConnectorSerializer
    search_fields = ["name"]
    ordering = ["name"]
    filterset_fields = ["name", "enabled"]

    @extend_schema(
        request=MDMConfigSerializer(),
        responses=MDMConfigResponseSerializer(),
    )
    @action(methods=["POST"], detail=True)
    def mdm_config(self, request: Request, pk) -> Response:
        """Generate configuration for MDM systems to deploy authentik Agent"""
        connector = cast(AgentConnector, self.get_object())
        data = MDMConfigSerializer(data=request.data, context={"connector": connector})
        data.is_valid(raise_exception=True)
        token = data.validated_data["enrollment_token"]
        if not request.user.has_perm("view_enrollment_token_key", token):
            raise PermissionDenied()
        ctrl = connector.controller(connector)
        payload = ctrl.generate_mdm_config(data.validated_data["platform"], request, token)
        return Response({"config": payload})

    @extend_schema(
        request=EnrollSerializer(),
        responses={200: AgentTokenResponseSerializer},
    )
    @action(
        methods=["POST"],
        detail=False,
        authentication_classes=[AgentEnrollmentAuth],
    )
    def enroll(self, request: Request):
        token: EnrollmentToken = request.auth
        data = EnrollSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        device, _ = Device.objects.get_or_create(
            identifier=data.validated_data["device_serial"],
            defaults={
                "name": data.validated_data["device_name"],
                "expiring": False,
                "access_group": token.device_group,
            },
        )
        connection, _ = AgentDeviceConnection.objects.update_or_create(
            device=device,
            connector=token.connector,
        )
        token = DeviceToken.objects.create(device=connection, expiring=False)
        return Response(
            {
                "token": token.key,
                "expires_in": 0,
            }
        )

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses=AgentConfigSerializer(),
    )
    @action(methods=["GET"], detail=False, authentication_classes=[AgentAuth])
    def agent_config(self, request: Request):
        token: DeviceToken = request.auth
        connector: AgentConnector = token.device.connector.agentconnector
        return Response(AgentConfigSerializer(connector, context={"request": request}).data)

    @extend_schema(
        request=DeviceFacts(),
        responses={204: OpenApiResponse(description="Successfully checked in")},
    )
    @action(methods=["POST"], detail=False, authentication_classes=[AgentAuth])
    def check_in(self, request: Request):
        token: DeviceToken = request.auth
        data = DeviceFacts(data=request.data)
        data.is_valid(raise_exception=True)
        connection: AgentDeviceConnection = token.device
        connection.create_snapshot(data.validated_data)
        return Response(status=204)
