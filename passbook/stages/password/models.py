"""password stage models"""
from typing import Optional

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.shortcuts import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from passbook.core.types import UIUserSettings
from passbook.flows.models import Flow, Stage
from passbook.flows.views import NEXT_ARG_NAME


class PasswordStage(Stage):
    """Prompts the user for their password, and validates it against the configured backends."""

    backends = ArrayField(
        models.TextField(),
        help_text=_("Selection of backends to test the password against."),
    )

    change_flow = models.ForeignKey(
        Flow,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_(
            (
                "Flow used by an authenticated user to change their password. "
                "If empty, user will be unable to change their password."
            )
        ),
    )

    type = "passbook.stages.password.stage.PasswordStage"
    form = "passbook.stages.password.forms.PasswordStageForm"

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        if not self.change_flow:
            return None
        base_url = reverse(
            "passbook_stages_password:change", kwargs={"stage_uuid": self.pk}
        )
        args = urlencode({NEXT_ARG_NAME: reverse("passbook_core:user-settings")})
        return UIUserSettings(name=_("Change password"), url=f"{base_url}?{args}")

    def __str__(self):
        return f"Password Stage {self.name}"

    class Meta:

        verbose_name = _("Password Stage")
        verbose_name_plural = _("Password Stages")
