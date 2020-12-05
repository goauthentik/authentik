"""authentik captcha stage"""
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


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

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.captcha.api import CaptchaStageSerializer

        return CaptchaStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.captcha.stage import CaptchaStageView

        return CaptchaStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.captcha.forms import CaptchaStageForm

        return CaptchaStageForm

    def __str__(self):
        return f"Captcha Stage {self.name}"

    class Meta:

        verbose_name = _("Captcha Stage")
        verbose_name_plural = _("Captcha Stages")
