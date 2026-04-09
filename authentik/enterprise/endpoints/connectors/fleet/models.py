from typing import TYPE_CHECKING

from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.endpoints.models import Connector

if TYPE_CHECKING:
    from authentik.enterprise.endpoints.connectors.fleet.controller import FleetController


class FleetConnector(Connector):
    """Ingest device data and policy compliance from a Fleet instance."""

    url = models.URLField()
    token = models.TextField()
    headers_mapping = models.ForeignKey(
        "authentik_events.NotificationWebhookMapping",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        related_name="+",
        help_text=_(
            "Configure additional headers to be sent. "
            "Mapping should return a dictionary of key-value pairs"
        ),
    )

    map_users = models.BooleanField(default=True)
    map_teams_access_group = models.BooleanField(default=False)

    @property
    def icon_url(self):
        return static("authentik/connectors/fleet.svg")

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.fleet.api import FleetConnectorSerializer

        return FleetConnectorSerializer

    @property
    def controller(self) -> type[FleetController]:
        from authentik.enterprise.endpoints.connectors.fleet.controller import FleetController

        return FleetController

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-fleet-form"

    class Meta:
        verbose_name = _("Fleet Connector")
        verbose_name_plural = _("Fleet Connectors")
