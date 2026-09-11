"""MicrosoftIntuneConnectorSerializer API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.endpoints.connectors.microsoft_intune.models import (
    MicrosoftIntuneConnector,
)


class MicrosoftIntuneConnectorSerializer(EnterpriseRequiredMixin, ConnectorSerializer):
    """MicrosoftIntuneConnector Serializer"""

    class Meta(ConnectorSerializer.Meta):
        model = MicrosoftIntuneConnector
        fields = ConnectorSerializer.Meta.fields + [
            "client_id",
            "client_secret",
            "tenant_id",
        ]
        extra_kwargs = {
            "client_secret": {"write_only": True},
        }


class MicrosoftIntuneConnectorViewSet(UsedByMixin, ModelViewSet):
    """MicrosoftIntuneConnector Viewset"""

    queryset = MicrosoftIntuneConnector.objects.all()
    serializer_class = MicrosoftIntuneConnectorSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
