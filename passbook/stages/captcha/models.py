"""passbook captcha stage"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import Stage


class CaptchaStage(Stage):
    """Verify the user is human using Google's reCaptcha."""

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

    type = "passbook.stages.captcha.stage.CaptchaStage"
    form = "passbook.stages.captcha.forms.CaptchaStageForm"

    def __str__(self):
        return f"Captcha Stage {self.name}"

    class Meta:

        verbose_name = _("Captcha Stage")
        verbose_name_plural = _("Captcha Stages")
