"""FleetConnector API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.enterprise.endpoints.connectors.fleet.models import (
    FleetConnector,
)


class FleetConnectorSerializer(ConnectorSerializer):
    """FleetConnector Serializer"""

    class Meta(ConnectorSerializer.Meta):
        model = FleetConnector
        fields = ConnectorSerializer.Meta.fields


class FleetConnectorViewSet(UsedByMixin, ModelViewSet):
    """FleetConnector Viewset"""

    queryset = FleetConnector.objects.all()
    serializer_class = FleetConnectorSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
