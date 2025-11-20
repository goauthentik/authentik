from typing import cast

from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.connectors.agent.auth import (
    AgentAuth,
    AgentEnrollmentAuth,
)
from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceToken, EnrollmentToken
from authentik.endpoints.facts import DeviceFacts, OSFamily
from authentik.endpoints.models import Device, DeviceConnection
from authentik.lib.utils.time import timedelta_from_string


class AgentConnectorSerializer(ConnectorSerializer):

    class Meta(ConnectorSerializer.Meta):
        model = AgentConnector
        fields = "__all__"


class AgentConfigSerializer(PassiveSerializer):

    nss_uid_offset = IntegerField()
    nss_gid_offset = IntegerField()
    authentication_flow = CharField()
    auth_terminate_session_on_expiry = BooleanField()
    refresh_interval = SerializerMethodField()

    def get_refresh_interval(self, instance: AgentConnector) -> int:
        return int(timedelta_from_string(instance.refresh_interval).total_seconds())


class EnrollSerializer(PassiveSerializer):

    device_serial = CharField()
    device_name = CharField()


class EnrollResponseSerializer(PassiveSerializer):

    token = CharField()


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


class AgentConnectorViewSet(UsedByMixin, ModelViewSet):

    queryset = AgentConnector.objects.all()
    serializer_class = AgentConnectorSerializer
    search_fields = ["name"]
    ordering = ["name"]
    filterset_fields = ["name", "enabled"]

    @extend_schema(
        request=EnrollSerializer(),
        responses={200: EnrollResponseSerializer},
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
                "group": token.device_group,
            },
        )
        connection, _ = DeviceConnection.objects.update_or_create(
            device=device,
            connector=token.connector,
        )
        token = DeviceToken.objects.create(device=connection, expiring=False)
        return Response(
            {
                "token": token.key,
            }
        )

    @extend_schema(
        responses=AgentConfigSerializer(),
        request=OpenApiTypes.NONE,
    )
    @action(methods=["GET"], detail=False, authentication_classes=[AgentAuth])
    def agent_config(self, request: Request):
        token: DeviceToken = request.auth
        connector: AgentConnector = token.device.connector.agentconnector
        return Response(AgentConfigSerializer(connector).data)

    @extend_schema(
        request=DeviceFacts(),
        responses={204: OpenApiResponse(description="Successfully checked in")},
    )
    @action(methods=["POST"], detail=False, authentication_classes=[AgentAuth])
    def check_in(self, request: Request):
        token: DeviceToken = request.auth
        data = DeviceFacts(data=request.data)
        data.is_valid(raise_exception=True)
        connection: DeviceConnection = token.device
        connection.create_snapshot(data.validated_data)
        return Response(status=204)

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
