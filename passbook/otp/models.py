"""OTP Factor"""

from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Factor


class OTPFactor(Factor):
    """OTP Factor"""

    enforced = models.BooleanField(default=False, help_text=('Enforce enabled OTP for Users '
                                                             'this factor applies to.'))

    type = 'passbook.otp.factors.OTPFactor'
    form = 'passbook.otp.forms.OTPFactorForm'

    def __str__(self):
        return "OTP Factor %s" % self.slug

    class Meta:

        verbose_name = _('OTP Factor')
        verbose_name_plural = _('OTP Factors')
