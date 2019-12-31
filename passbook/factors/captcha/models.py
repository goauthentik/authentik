"""passbook captcha factor"""
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Factor


class CaptchaFactor(Factor):
    """Captcha Factor instance"""

    public_key = models.TextField()
    private_key = models.TextField()

    type = "passbook.factors.captcha.factor.CaptchaFactor"
    form = "passbook.factors.captcha.forms.CaptchaFactorForm"

    def __str__(self):
        return f"Captcha Factor {self.slug}"

    class Meta:

        verbose_name = _("Captcha Factor")
        verbose_name_plural = _("Captcha Factors")
