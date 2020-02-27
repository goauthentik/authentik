"""passbook captcha factor"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.core.models import Factor


class CaptchaFactor(Factor):
    """Captcha Factor instance"""

    public_key = models.TextField(
        help_text=_(
            "Public key, acquired from https://www.google.com/recaptcha/intro/v3.html"
        )
    )
    private_key = models.TextField(
        help_text=_(
            "Private key, acquired from https://www.google.com/recaptcha/intro/v3.html"
        )
    )

    type = "passbook.factors.captcha.factor.CaptchaFactor"
    form = "passbook.factors.captcha.forms.CaptchaFactorForm"

    def __str__(self):
        return f"Captcha Factor {self.slug}"

    class Meta:

        verbose_name = _("Captcha Factor")
        verbose_name_plural = _("Captcha Factors")
