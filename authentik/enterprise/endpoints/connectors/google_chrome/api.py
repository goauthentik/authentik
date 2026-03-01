"""GoogleChromeConnector API Views"""

from django.urls import reverse
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector


class GoogleChromeConnectorSerializer(EnterpriseRequiredMixin, ConnectorSerializer):
    """GoogleChromeConnector Serializer"""

    chrome_url = SerializerMethodField()

    def get_chrome_url(self, _: GoogleChromeConnector) -> str | None:
        """Full URL to be used in Google Workspace configuration"""
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return request.build_absolute_uri(
            reverse("authentik_endpoints_connectors_google_chrome:chrome")
        )

    class Meta:
        model = GoogleChromeConnector
        fields = ConnectorSerializer.Meta.fields + ["credentials", "chrome_url"]


class GoogleChromeConnectorViewSet(UsedByMixin, ModelViewSet):
    """GoogleChromeConnector Viewset"""

    queryset = GoogleChromeConnector.objects.all()
    serializer_class = GoogleChromeConnectorSerializer
    filterset_fields = [
        "name",
    ]
    search_fields = ["name"]
    ordering = ["name"]
