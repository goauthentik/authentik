from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.models import EndpointStage
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.flows.api.stages import StageSerializer


class EndpointStageSerializer(EnterpriseRequiredMixin, StageSerializer):
    """EndpointStage Serializer"""

    connector_obj = ConnectorSerializer(source="connector", read_only=True)

    class Meta:
        model = EndpointStage
        fields = StageSerializer.Meta.fields + [
            "connector",
            "connector_obj",
        ]


class EndpointStageViewSet(UsedByMixin, ModelViewSet):
    """EndpointStage Viewset"""

    queryset = EndpointStage.objects.all()
    serializer_class = EndpointStageSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
