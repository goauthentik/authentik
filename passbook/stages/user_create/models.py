"""create stage models"""
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class UserCreateStage(Stage):
    """Create stage, create a user from saved data."""

    type = "passbook.stages.user_create.stage.UserCreateStageView"
    form = "passbook.stages.user_create.forms.UserCreateStageForm"

    def __str__(self):
        return f"User Create Stage {self.name}"

    class Meta:

        verbose_name = _("User Create Stage")
        verbose_name_plural = _("User Create Stages")
