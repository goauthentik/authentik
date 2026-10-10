from typing import TYPE_CHECKING

from azure.identity import ClientSecretCredential
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.models import Connector
from authentik.lib.models import SimpleThroughModel

if TYPE_CHECKING:
    from authentik.enterprise.endpoints.connectors.microsoft_intune.controller import (
        MicrosoftIntuneController,
    )


class MicrosoftIntuneConnector(Connector):
    """Sync device details from Microsoft Intune"""

    client_id = models.TextField()
    client_secret = models.TextField()
    tenant_id = models.TextField()

    certificate_authorities = models.ManyToManyField(
        CertificateKeyPair,
        default=None,
        blank=True,
        help_text=_(
            "Certificate authorities which issue device certificates via Intune (Cloud PKI, "
            "SCEP or PKCS profiles), used by the endpoint stage to validate certificates. "
            "This option has a higher priority than the `client_certificate` option on `Brand`."
        ),
        through="MicrosoftIntuneConnectorCertificateAuthority",
    )

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
    def stage(self):
        from authentik.enterprise.endpoints.connectors.microsoft_intune.stage import (
            MicrosoftIntuneStageView,
        )

        return MicrosoftIntuneStageView

    @property
    def icon_url(self):
        return static("authentik/sources/entraid.svg")

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-microsoft-intune-form"

    class Meta:
        verbose_name = _("Microsoft Intune Connector")
        verbose_name_plural = _("Microsoft Intune Connectors")


class MicrosoftIntuneConnectorCertificateAuthority(SimpleThroughModel):
    connector = models.ForeignKey(MicrosoftIntuneConnector, on_delete=models.CASCADE)
    certificate_key_pair = models.ForeignKey(CertificateKeyPair, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("connector", "certificate_key_pair"),)
        verbose_name = _("Microsoft Intune Connector Certificate Authority")
        verbose_name_plural = _("Microsoft Intune Connector Certificate Authorities")

    def __str__(self):
        return (
            "MicrosoftIntuneConnectorCertificateAuthority for MicrosoftIntuneConnector "
            f"{self.connector_id} and CertificateKeyPair {self.certificate_key_pair_id}."
        )
