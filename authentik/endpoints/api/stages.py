from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.controller import Capabilities
from authentik.endpoints.models import Connector, EndpointStage
from authentik.flows.api.stages import StageSerializer


class EndpointStageSerializer(StageSerializer):
    """EndpointStage Serializer"""

    connector_obj = ConnectorSerializer(source="connector", read_only=True)

    def validate_connector(self, connector: Connector) -> Connector:
        conn: Connector = Connector.objects.get_subclass(pk=connector.pk)
        controller = conn.controller(conn)
        if Capabilities.STAGE_ENDPOINTS not in controller.capabilities():
            raise ValidationError(_("Selected connector is not comaptible with this stage."))
        return connector

    class Meta:
        model = EndpointStage
        fields = StageSerializer.Meta.fields + [
            "connector",
            "connector_obj",
            "mode",
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
