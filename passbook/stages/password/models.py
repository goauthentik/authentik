"""password stage models"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class PasswordStage(Stage):
    """Password-based Django-backend Authentication Stage"""

    backends = ArrayField(
        models.TextField(),
        help_text=_("Selection of backends to test the password against."),
    )

    type = "passbook.stages.password.stage.PasswordStage"
    form = "passbook.stages.password.forms.PasswordStageForm"

    def __str__(self):
        return f"Password Stage {self.name}"

    class Meta:

        verbose_name = _("Password Stage")
        verbose_name_plural = _("Password Stages")
