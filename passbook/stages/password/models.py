"""password stage models"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Policy, User
from passbook.core.types import UIUserSettings
from passbook.flows.models import Stage


class PasswordStage(Stage):
    """Password-based Django-backend Authentication Stage"""

    backends = ArrayField(
        models.TextField(),
        help_text=_("Selection of backends to test the password against."),
    )
    password_policies = models.ManyToManyField(Policy, blank=True)

    type = "passbook.stages.password.stage.PasswordStage"
    form = "passbook.stages.password.forms.PasswordStageForm"

    @property
    def ui_user_settings(self) -> UIUserSettings:
        return UIUserSettings(
            name="Change Password",
            icon="pficon-key",
            view_name="passbook_core:user-change-password",
        )

    def password_passes(self, user: User) -> bool:
        """Return true if user's password passes, otherwise False or raise Exception"""
        for policy in self.policies.all():
            if not policy.passes(user):
                return False
        return True

    def __str__(self):
        return f"Password Stage {self.name}"

    class Meta:

        verbose_name = _("Password Stage")
        verbose_name_plural = _("Password Stages")
