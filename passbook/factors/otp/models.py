"""OTP Factor"""

from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Factor, UserSettings


class OTPFactor(Factor):
    """OTP Factor"""

    enforced = models.BooleanField(
        default=False,
        help_text=("Enforce enabled OTP for Users " "this factor applies to."),
    )

    type = "passbook.factors.otp.factors.OTPFactor"
    form = "passbook.factors.otp.forms.OTPFactorForm"

    def user_settings(self) -> UserSettings:
        return UserSettings(
            _("OTP"), "pficon-locked", "passbook_factors_otp:otp-user-settings"
        )

    def __str__(self):
        return f"OTP Factor {self.slug}"

    class Meta:

        verbose_name = _("OTP Factor")
        verbose_name_plural = _("OTP Factors")
