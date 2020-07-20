"""OTP Time-based models"""
from typing import Optional, Type

from django.db import models
from django.forms import ModelForm
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

from passbook.core.types import UIUserSettings
from passbook.flows.models import Stage


class TOTPDigits(models.IntegerChoices):
    """OTP Time Digits"""

    SIX = 6, _("6 digits, widely compatible")
    EIGHT = 8, _("8 digits, not compatible with apps like Google Authenticator")


class OTPTimeStage(Stage):
    """Enroll a user's device into Time-based OTP."""

    digits = models.IntegerField(choices=TOTPDigits.choices)

    def type(self) -> Type[View]:
        from passbook.stages.otp_time.stage import OTPTimeStageView

        return OTPTimeStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.otp_time.forms import OTPTimeStageForm

        return OTPTimeStageForm

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        return UIUserSettings(
            name="Time-based OTP",
            url=reverse("passbook_stages_otp_time:user-settings"),
        )

    def __str__(self) -> str:
        return f"OTP Time (TOTP) Stage {self.name}"

    class Meta:

        verbose_name = _("OTP Time (TOTP) Setup Stage")
        verbose_name_plural = _("OTP Time (TOTP) Setup Stages")
