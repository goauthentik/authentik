"""login stage models"""
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class LoginStage(Stage):
    """Login stage, allows a user to identify themselves to authenticate."""

    type = "passbook.stages.login.stage.LoginStageView"
    form = "passbook.stages.login.forms.LoginStageForm"

    def __str__(self):
        return f"Login Stage {self.name}"

    class Meta:

        verbose_name = _("Login Stage")
        verbose_name_plural = _("Login Stages")
