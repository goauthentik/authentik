from django.db import models

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Stage


class TLSMode(models.TextChoices):

    OPTIONAL = "optional"
    REQUIRED_ANY = "required_any"
    REQUIRED_AUTH = "required_auth"
    REQUIRED_ENROLL = "required_enroll"


class CertAttributes(models.TextChoices):

    SUBJECT = "subject"
    COMMON_NAME = "common_name"
    EMAIL = "email"


class UserAttributes(models.TextChoices):

    USERNAME = "username"
    EMAIL = "email"


class MutualTLSStage(Stage):

    mode = models.TextField(choices=TLSMode.choices)

    certificate_authority = models.ForeignKey(
        CertificateKeyPair, on_delete=models.SET_DEFAULT, default=None, null=True
    )

    cert_attribute = models.TextField(choices=CertAttributes.choices)
    user_attribute = models.TextField(choices=UserAttributes.choices)
