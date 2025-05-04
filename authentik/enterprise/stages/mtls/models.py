from django.db import models
from rest_framework.serializers import Serializer

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Stage
from authentik.flows.stage import StageView


class TLSMode(models.TextChoices):
    """Modes the TLS Stage can operate in"""

    OPTIONAL = "optional"
    REQUIRED_ANY = "required_any"
    REQUIRED_AUTH = "required_auth"
    REQUIRED_ENROLL = "required_enroll"


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
    """Client-certificate/mTLS authentication/enrollment"""

    mode = models.TextField(choices=TLSMode.choices)

    certificate_authority = models.ForeignKey(
        CertificateKeyPair, on_delete=models.SET_DEFAULT, default=None, null=True
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
