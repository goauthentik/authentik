"""OTP Time-based models"""
from typing import Optional

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage


class TOTPDigits(models.IntegerChoices):
    """OTP Time Digits"""

    SIX = 6, _("6 digits, widely compatible")
    EIGHT = 8, _("8 digits, not compatible with apps like Google Authenticator")


class AuthenticatorTOTPStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Enroll a user's device into Time-based OTP."""

    digits = models.IntegerField(choices=TOTPDigits.choices)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_totp.api import AuthenticatorTOTPStageSerializer

        return AuthenticatorTOTPStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_totp.stage import AuthenticatorTOTPStageView

        return AuthenticatorTOTPStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-totp-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-totp",
            }
        )

    def __str__(self) -> str:
        return f"TOTP Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("TOTP Authenticator Setup Stage")
        verbose_name_plural = _("TOTP Authenticator Setup Stages")
