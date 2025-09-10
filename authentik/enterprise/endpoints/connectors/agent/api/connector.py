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
