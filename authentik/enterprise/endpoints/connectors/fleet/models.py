from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _
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

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-fleet"

    class Meta:
        verbose_name = _("Fleet Connector")
        verbose_name_plural = _("Fleet Connectors")
