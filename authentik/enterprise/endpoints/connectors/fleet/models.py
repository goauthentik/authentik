from django.db import models
from rest_framework.serializers import Serializer

from authentik.endpoints.models import Connector


class FleetConnector(Connector):
    url = models.URLField()
    token = models.TextField()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.fleet.api import FleetConnectorSerializer

        return FleetConnectorSerializer
