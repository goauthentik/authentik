from typing import cast

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import ChoiceField
from rest_framework.permissions import IsAuthenticated
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
    DeviceAuthFedAuthentication,
    agent_auth_issue_token,
    check_device_policies,
)
from authentik.endpoints.connectors.agent.controller import MDMConfigResponseSerializer
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    DeviceToken,
    EnrollmentToken,
)
from authentik.endpoints.facts import DeviceFacts, OSFamily
from authentik.endpoints.models import Device
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.lib.utils.reflection import ConditionalInheritance
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS


class AgentConnectorSerializer(ConnectorSerializer):

    class Meta(ConnectorSerializer.Meta):
        model = AgentConnector
        fields = ConnectorSerializer.Meta.fields + [
            "snapshot_expiry",
            "auth_session_duration",
            "auth_terminate_session_on_expiry",
            "refresh_interval",
            "authorization_flow",
            "nss_uid_offset",
            "nss_gid_offset",
            "challenge_key",
            "challenge_idle_timeout",
            "challenge_trigger_check_in",
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
        return Response(payload.validated_data)

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
        DeviceToken.objects.filter(device=connection).delete()
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
        return Response(
            AgentConfigSerializer(
                connector, context={"request": request, "device": token.device.device}
            ).data
        )

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

    @extend_schema(
        request=OpenApiTypes.NONE,
        parameters=[OpenApiParameter("device", OpenApiTypes.STR, location="query", required=True)],
        responses={
            200: AgentTokenResponseSerializer(),
            404: OpenApiResponse(description="Device not found"),
        },
    )
    @action(
        methods=["POST"],
        detail=False,
        pagination_class=None,
        filter_backends=[],
        permission_classes=[IsAuthenticated],
        authentication_classes=[DeviceAuthFedAuthentication],
    )
    def auth_fed(self, request: Request) -> Response:
        federated_token, device, connector = request.auth

        policy_result = check_device_policies(device, federated_token.user, request._request)
        if not policy_result.passing:
            raise ValidationError(
                {"policy_result": "Policy denied access", "policy_messages": policy_result.messages}
            )

        token, exp = agent_auth_issue_token(device, connector, federated_token.user)
        rel_exp = int((exp - now()).total_seconds())
        Event.new(
            EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "jwt",
                PLAN_CONTEXT_METHOD_ARGS: {
                    "jwt": federated_token,
                    "provider": federated_token.provider,
                },
                PLAN_CONTEXT_DEVICE: device,
            },
        ).from_http(request, user=federated_token.user)
        return Response({"token": token, "expires_in": rel_exp})
