"""OTP Validation Stage"""
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View

from passbook.flows.models import NotConfiguredAction, Stage


class OTPValidateStage(Stage):
    """Validate user's configured OTP Device."""

    not_configured_action = models.TextField(
        choices=NotConfiguredAction.choices, default=NotConfiguredAction.SKIP
    )

    def type(self) -> Type[View]:
        from passbook.stages.otp_validate.stage import OTPValidateStageView

        return OTPValidateStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.otp_validate.forms import OTPValidateStageForm

        return OTPValidateStageForm

    def __str__(self) -> str:
        return f"OTP Validation Stage {self.name}"

    class Meta:

        verbose_name = _("OTP Validation Stage")
        verbose_name_plural = _("OTP Validation Stages")
