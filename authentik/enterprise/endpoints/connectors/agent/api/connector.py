from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.endpoints.connectors.agent.models import AgentConnector


class AgentConnectorSerializer(ModelSerializer):

    class Meta:
        model = AgentConnector
        fields = "__all__"


class AgentConnectorViewSet(UsedByMixin, ModelViewSet):

    queryset = AgentConnector.objects.all()
    serializer_class = AgentConnectorSerializer

    @action(methods=["POST"], detail=True)
    @extend_schema(
        request=OpenApiTypes.OBJECT,
    )
    def report(self, request: Request):
        pass
