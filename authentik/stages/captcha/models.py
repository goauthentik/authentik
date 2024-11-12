"""authentik captcha stage"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class CaptchaStage(Stage):
    """Verify the user is human using Google's reCaptcha/other compatible CAPTCHA solutions."""

    public_key = models.TextField(help_text=_("Public key, acquired your captcha Provider."))
    private_key = models.TextField(help_text=_("Private key, acquired your captcha Provider."))

    interactive = models.BooleanField(default=False)

    score_min_threshold = models.FloatField(default=0.5)  # Default values for reCaptcha
    score_max_threshold = models.FloatField(default=1.0)  # Default values for reCaptcha

    error_on_invalid_score = models.BooleanField(
        default=True,
        help_text=_(
            "When enabled and the received captcha score is outside of the given threshold, "
            "the stage will show an error message. When not enabled, the flow will continue, "
            "but the data from the captcha will be available in the context for policy decisions"
        ),
    )

    js_url = models.TextField(default="https://www.recaptcha.net/recaptcha/api.js")
    api_url = models.TextField(default="https://www.recaptcha.net/recaptcha/api/siteverify")

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.captcha.api import CaptchaStageSerializer

        return CaptchaStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.captcha.stage import CaptchaStageView

        return CaptchaStageView

    @property
    def component(self) -> str:
        return "ak-stage-captcha-form"

    class Meta:
        verbose_name = _("Captcha Stage")
        verbose_name_plural = _("Captcha Stages")
