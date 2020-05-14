"""logout stage models"""
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class UserLogoutStage(Stage):
    """Logout stage, allows a user to identify themselves to authenticate."""

    type = "passbook.stages.user_logout.stage.UserLogoutStageView"
    form = "passbook.stages.user_logout.forms.UserLogoutStageForm"

    def __str__(self):
        return f"User Logout Stage {self.name}"

    class Meta:

        verbose_name = _("User Logout Stage")
        verbose_name_plural = _("User Logout Stages")
