from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, IntegerField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.endpoints.connectors.agent.api._auth import (
    authenticate_device,
    authenticate_enrollment,
)
from authentik.endpoints.connectors.agent.models import AgentConnector, DeviceToken
from authentik.endpoints.facts import DeviceFacts
from authentik.endpoints.models import Device, DeviceConnection


class AgentConnectorSerializer(ModelSerializer):

    class Meta:
        model = AgentConnector
        fields = "__all__"


class AgentConfigSerializer(PassiveSerializer):

    nss_uid_offset = IntegerField()
    nss_gid_offset = IntegerField()
    authentication_flow = CharField()


class EnrollSerializer(PassiveSerializer):

    device_serial = CharField()
    device_name = CharField()


class EnrollResponseSerializer(PassiveSerializer):

    token = CharField()


class AgentConnectorViewSet(UsedByMixin, ModelViewSet):

    queryset = AgentConnector.objects.all()
    serializer_class = AgentConnectorSerializer

    @extend_schema(
        request=DeviceFacts(),
        responses={201: OpenApiResponse(description="Report created.")},
    )
    @action(methods=["POST"], detail=False)
    def report(self, request: Request):
        Device.objects.get_or_create()

    @extend_schema(
        responses=AgentConfigSerializer(),
        request=OpenApiTypes.NONE,
    )
    @action(methods=["GET"], detail=False, authentication_classes=[], permission_classes=[])
    def agent_config(self, request: Request):
        token = authenticate_device(request)
        connector: AgentConnector = token.device.connector.agentconnector
        return Response(AgentConfigSerializer(connector).data)

    @extend_schema(
        request=EnrollSerializer(),
        parameters=[OpenApiParameter("authorization", OpenApiTypes.STR, location="header")],
        responses={200: EnrollResponseSerializer},
    )
    @action(methods=["POST"], detail=False, authentication_classes=[], permission_classes=[])
    def enroll(self, request: Request):
        connector = authenticate_enrollment(request)
        data = EnrollSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        device, _ = Device.objects.get_or_create(
            identifier=data.validated_data["device_serial"],
            defaults={
                "name": data.validated_data["device_name"],
            },
        )
        connection, _ = DeviceConnection.objects.update_or_create(
            device=device,
            connector=connector,
            create_defaults={
                "data": {},
            },
        )
        token = DeviceToken.objects.create(device=connection, expires=False)
        return Response(
            {
                "token": token.key,
            }
        )
