from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.endpoints.models import Connector

if TYPE_CHECKING:
    from authentik.enterprise.endpoints.connectors.fleet.controller import FleetController


class FleetConnector(Connector):
    """Ingest device data and policy compliance from a Fleet instance."""

    url = models.URLField()
    token = models.TextField()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.fleet.api import FleetConnectorSerializer

        return FleetConnectorSerializer

    @property
    def controller(self) -> type["FleetController"]:
        from authentik.enterprise.endpoints.connectors.fleet.controller import FleetController

        return FleetController

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-fleet-form"

    class Meta:
        verbose_name = _("Fleet Connector")
        verbose_name_plural = _("Fleet Connectors")
