from typing import TYPE_CHECKING

from django.db import models
from rest_framework.serializers import Serializer

from authentik.endpoints.models import Connector

if TYPE_CHECKING:
    from authentik.enterprise.endpoints.connectors.fleet.connector import FleetConnector


class FleetConnector(Connector):
    url = models.URLField()
    token = models.TextField()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.fleet.api import FleetConnectorSerializer

        return FleetConnectorSerializer

    @property
    def controller(self) -> type["FleetConnector"]:
        from authentik.enterprise.endpoints.connectors.fleet.connector import FleetConnector

        return FleetConnector
