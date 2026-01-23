"""GoogleChromeConnector API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector


class GoogleChromeConnectorSerializer(EnterpriseRequiredMixin, ConnectorSerializer):
    """GoogleChromeConnector Serializer"""

    class Meta:
        model = GoogleChromeConnector
        fields = ConnectorSerializer.Meta.fields + [
            "credentials",
        ]


class GoogleChromeConnectorViewSet(UsedByMixin, ModelViewSet):
    """GoogleChromeConnector Viewset"""

    queryset = GoogleChromeConnector.objects.all()
    serializer_class = GoogleChromeConnectorSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
