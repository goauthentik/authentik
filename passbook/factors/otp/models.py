"""OTP Factor"""
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.types import UIUserSettings
from passbook.core.models import Factor


class OTPFactor(Factor):
    """OTP Factor"""

    enforced = models.BooleanField(
        default=False,
        help_text=("Enforce enabled OTP for Users " "this factor applies to."),
    )

    type = "passbook.factors.otp.factors.OTPFactor"
    form = "passbook.factors.otp.forms.OTPFactorForm"

    @property
    def ui_user_settings(self) -> UIUserSettings:
        return UIUserSettings(
            name="OTP",
            icon="pficon-locked",
            view_name="passbook_factors_otp:otp-user-settings",
        )

    def __str__(self):
        return f"OTP Factor {self.slug}"

    class Meta:

        verbose_name = _("OTP Factor")
        verbose_name_plural = _("OTP Factors")
