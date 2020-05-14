"""write stage models"""
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class UserWriteStage(Stage):
    """Write stage, write a user from saved data."""

    type = "passbook.stages.user_write.stage.UserWriteStageView"
    form = "passbook.stages.user_write.forms.UserWriteStageForm"

    def __str__(self):
        return f"User Write Stage {self.name}"

    class Meta:

        verbose_name = _("User Write Stage")
        verbose_name_plural = _("User Write Stages")
