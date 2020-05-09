"""identification stage models"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class UserFields(models.TextChoices):
    """Fields which the user can identify themselves with"""

    E_MAIL = "email"
    USERNAME = "username"


class Templates(models.TextChoices):
    """Templates to be used for the stage"""

    DEFAULT_LOGIN = "login/form.html"


class IdentificationStage(Stage):
    """Identification stage, allows a user to identify themselves to authenticate."""

    user_fields = ArrayField(
        models.CharField(max_length=100, choices=UserFields.choices),
        help_text=_("Fields of the user object to match against."),
    )
    template = models.TextField(choices=Templates.choices)

    type = "passbook.stages.identification.stage.IdentificationStageView"
    form = "passbook.stages.identification.forms.IdentificationStageForm"

    def __str__(self):
        return f"Identification Stage {self.name}"

    class Meta:

        verbose_name = _("Identification Stage")
        verbose_name_plural = _("Identification Stages")
