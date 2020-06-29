"""OTP Stage"""
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

from passbook.core.types import UIUserSettings
from passbook.flows.models import Stage


class OTPStage(Stage):
    """OTP Stage"""

    enforced = models.BooleanField(
        default=False,
        help_text=("Enforce enabled OTP for Users " "this stage applies to."),
    )

    type = "passbook.stages.otp.stages.OTPStage"
    form = "passbook.stages.otp.forms.OTPStageForm"

    @property
    def ui_user_settings(self) -> UIUserSettings:
        return UIUserSettings(
            name="OTP", url=reverse("passbook_stages_otp:otp-user-settings"),
        )

    def __str__(self):
        return f"OTP Stage {self.name}"

    class Meta:

        verbose_name = _("OTP Stage")
        verbose_name_plural = _("OTP Stages")
