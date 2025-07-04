"""GoogleChromeConnector API Views"""

from rest_framework import mixins
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.endpoints.connectors.google_chrome.models import (
    GoogleChromeConnector,
)
from authentik.flows.api.stages import StageSerializer

LOGGER = get_logger()


class GoogleChromeConnectorSerializer(EnterpriseRequiredMixin, StageSerializer):
    """GoogleChromeConnector Serializer"""

    class Meta:
        model = GoogleChromeConnector
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "credentials",
        ]


class GoogleChromeConnectorViewSet(UsedByMixin, ModelViewSet):
    """GoogleChromeConnector Viewset"""

    queryset = GoogleChromeConnector.objects.all()
    serializer_class = GoogleChromeConnectorSerializer
    filterset_fields = [
        "name",
        "configure_flow",
    ]
    search_fields = ["name"]
    ordering = ["name"]
