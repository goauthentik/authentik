"""OTP Time-based models"""
from typing import Optional, Type

from django.db import models
from django.forms import ModelForm
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import ConfigurableStage, Stage


class TOTPDigits(models.IntegerChoices):
    """OTP Time Digits"""

    SIX = 6, _("6 digits, widely compatible")
    EIGHT = 8, _("8 digits, not compatible with apps like Google Authenticator")


class AuthenticatorTOTPStage(ConfigurableStage, Stage):
    """Enroll a user's device into Time-based OTP."""

    digits = models.IntegerField(choices=TOTPDigits.choices)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_totp.api import (
            AuthenticatorTOTPStageSerializer,
        )

        return AuthenticatorTOTPStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.authenticator_totp.stage import AuthenticatorTOTPStageView

        return AuthenticatorTOTPStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.authenticator_totp.forms import AuthenticatorTOTPStageForm

        return AuthenticatorTOTPStageForm

    @property
    def ui_user_settings(self) -> Optional[str]:
        return reverse(
            "authentik_stages_authenticator_totp:user-settings",
            kwargs={"stage_uuid": self.stage_uuid},
        )

    def __str__(self) -> str:
        return f"TOTP Authenticator Setup Stage {self.name}"

    class Meta:

        verbose_name = _("TOTP Authenticator Setup Stage")
        verbose_name_plural = _("TOTP Authenticator Setup Stages")
