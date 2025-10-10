from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.endpoints.common_data import CommonDeviceDataSerializer, HardwareSerializer
from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.agent.models import AgentConnector


class AgentConnectorSerializer(ModelSerializer):

    class Meta:
        model = AgentConnector
        fields = "__all__"


class EnrollSerializer(PassiveSerializer):

    enrollment_token = CharField()
    device = HardwareSerializer()

class EnrollResponseSerializer(PassiveSerializer):

    token = CharField()


class AgentConnectorViewSet(UsedByMixin, ModelViewSet):

    queryset = AgentConnector.objects.all()
    serializer_class = AgentConnectorSerializer

    @extend_schema(
        request=CommonDeviceDataSerializer(),
        responses={201: OpenApiResponse(description="Report created.")},
    )
    @action(methods=["POST"], detail=False)
    def report(self, request: Request):
        Device.objects.get_or_create(

        )

    @extend_schema(request=EnrollSerializer(), responses={200: EnrollResponseSerializer})
    @action(methods=["POST"], detail=False)
    def enroll(self, request: Request):
        data = EnrollSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        Device.objects.get_or_create(
            identifier=data.validated_data["device"]["serial"],

        )
