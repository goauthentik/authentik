"""authentik captcha stage"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class CaptchaStage(Stage):
    """Verify the user is human using Google's reCaptcha."""

    public_key = models.TextField(
        help_text=_("Public key, acquired from https://www.google.com/recaptcha/intro/v3.html")
    )
    private_key = models.TextField(
        help_text=_("Private key, acquired from https://www.google.com/recaptcha/intro/v3.html")
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.captcha.api import CaptchaStageSerializer

        return CaptchaStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.captcha.stage import CaptchaStageView

        return CaptchaStageView

    @property
    def component(self) -> str:
        return "ak-stage-captcha-form"

    class Meta:

        verbose_name = _("Captcha Stage")
        verbose_name_plural = _("Captcha Stages")
