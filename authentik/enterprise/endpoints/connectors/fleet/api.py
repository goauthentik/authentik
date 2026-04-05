"""FleetConnector API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.endpoints.connectors.fleet.models import FleetConnector


class FleetConnectorSerializer(EnterpriseRequiredMixin, ConnectorSerializer):
    """FleetConnector Serializer"""

    class Meta(ConnectorSerializer.Meta):
        model = FleetConnector
        fields = ConnectorSerializer.Meta.fields + [
            "url",
            "token",
            "headers_mapping",
            "map_users",
            "map_teams_access_group",
        ]
        extra_kwargs = {
            "token": {"write_only": True},
        }


class FleetConnectorViewSet(UsedByMixin, ModelViewSet):
    """FleetConnector Viewset"""

    queryset = FleetConnector.objects.all()
    serializer_class = FleetConnectorSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
