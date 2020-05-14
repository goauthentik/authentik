"""delete stage models"""
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class UserDeleteStage(Stage):
    """Delete stage, delete a user from saved data."""

    type = "passbook.stages.user_delete.stage.UserDeleteStageView"
    form = "passbook.stages.user_delete.forms.UserDeleteStageForm"

    def __str__(self):
        return f"User Delete Stage {self.name}"

    class Meta:

        verbose_name = _("User Delete Stage")
        verbose_name_plural = _("User Delete Stages")
