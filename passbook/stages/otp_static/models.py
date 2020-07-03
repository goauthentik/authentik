"""OTP Static models"""
from typing import Optional

from django.db import models
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _

from passbook.core.types import UIUserSettings
from passbook.flows.models import Stage


class OTPStaticStage(Stage):
    """Generate static tokens for the user as a backup."""

    token_count = models.IntegerField(default=6)

    type = "passbook.stages.otp_static.stage.OTPStaticStageView"
    form = "passbook.stages.otp_static.forms.OTPStaticStageForm"

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        return UIUserSettings(
            name="Static OTP", url=reverse("passbook_stages_otp_static:user-settings"),
        )

    def __str__(self) -> str:
        return f"OTP Static Stage {self.name}"

    class Meta:

        verbose_name = _("OTP Static Setup Stage")
        verbose_name_plural = _("OTP Static Setup Stages")
