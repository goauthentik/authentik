from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Stage
from authentik.flows.stage import StageView


class TLSMode(models.TextChoices):
    """Modes the TLS Stage can operate in"""

    OPTIONAL = "optional"
    REQUIRED = "required"


class CertAttributes(models.TextChoices):
    """Certificate attribute used for user matching"""

    SUBJECT = "subject"
    COMMON_NAME = "common_name"
    EMAIL = "email"


class UserAttributes(models.TextChoices):
    """User attribute for user matching"""

    USERNAME = "username"
    EMAIL = "email"


class MutualTLSStage(Stage):
    """Authenticate/enroll users using a client-certificate."""

    mode = models.TextField(choices=TLSMode.choices)

    certificate_authorities = models.ManyToManyField(
        CertificateKeyPair,
        default=None,
        blank=True,
        help_text=_(
            "Configure certificate authorities to validate the certificate against. "
            "This option has a higher priority than the `client_certificate` option on `Brand`."
        ),
    )

    cert_attribute = models.TextField(choices=CertAttributes.choices)
    user_attribute = models.TextField(choices=UserAttributes.choices)

    @property
    def view(self) -> type[StageView]:
        from authentik.enterprise.stages.mtls.stage import MTLSStageView

        return MTLSStageView

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.stages.mtls.api import MutualTLSStageSerializer

        return MutualTLSStageSerializer

    @property
    def component(self) -> str:
        return "ak-stage-mtls-form"

    class Meta:
        verbose_name = _("Mutual TLS Stage")
        verbose_name_plural = _("Mutual TLS Stages")
        permissions = [
            ("pass_outpost_certificate", _("Permissions to pass Certificates for outposts.")),
        ]
