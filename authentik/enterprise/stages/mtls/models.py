from django.db import models

from authentik.flows.models import Stage


class TLSMode(models.TextChoices):

    OPTIONAL = "optional"
    REQUIRED = "required"


class CertAttributes(models.TextChoices):

    SUBJECT = "subject"
    COMMON_NAME = "common_name"
    # [...]

class UserAttributes(models.TextChoices):

    USERNAME = "username"
    EMAIL = "email"
    # [...]

class MutualTLSStage(Stage):

    cert_attribute = models.TextField(choices=CertAttributes.choices)
    user_attribute = models.TextField(choices=UserAttributes.choices)

    mode = models.TextField(choices=TLSMode.choices)
