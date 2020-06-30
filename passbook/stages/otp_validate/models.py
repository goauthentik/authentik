"""OTP Validation Stage"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.flows.models import NotConfiguredAction, Stage


class OTPValidateStage(Stage):
    """Validate user's configured OTP Device"""

    not_configured_action = models.TextField(
        choices=NotConfiguredAction.choices, default=NotConfiguredAction.SKIP
    )

    type = "passbook.stages.otp_validate.stage.OTPValidateStageView"
    form = "passbook.stages.otp_validate.forms.OTPValidateStageForm"

    def __str__(self) -> str:
        return f"OTP Validation Stage {self.name}"

    class Meta:

        verbose_name = _("OTP Validation Stage")
        verbose_name_plural = _("OTP Validation Stages")
