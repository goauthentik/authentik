from typing import TYPE_CHECKING

from azure.identity import ClientSecretCredential
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from authentik.endpoints.models import Connector

if TYPE_CHECKING:
    from authentik.enterprise.endpoints.connectors.microsoft_intune.controller import (
        MicrosoftIntuneController,
    )


class MicrosoftIntuneConnector(Connector):
    """Sync device details from Microsoft Intune"""

    client_id = models.TextField()
    client_secret = models.TextField()
    tenant_id = models.TextField()

    def microsoft_credentials(self):
        return {
            "credentials": ClientSecretCredential(
                self.tenant_id, self.client_id, self.client_secret
            )
        }

    @property
    def serializer(self):
        from authentik.enterprise.endpoints.connectors.microsoft_intune.api import (
            MicrosoftIntuneConnectorSerializer,
        )

        return MicrosoftIntuneConnectorSerializer

    @property
    def controller(self) -> type[MicrosoftIntuneController]:
        from authentik.enterprise.endpoints.connectors.microsoft_intune.controller import (
            MicrosoftIntuneController,
        )

        return MicrosoftIntuneController

    @property
    def icon_url(self):
        return static("authentik/sources/entraid.svg")

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-microsoft-intune-form"

    class Meta:
        verbose_name = _("Microsoft Intune Connector")
        verbose_name_plural = _("Microsoft Intune Connectors")
