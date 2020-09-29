"""OTP Static models"""
from typing import Optional, Type

from django.db import models
from django.forms import ModelForm
from django.shortcuts import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from passbook.core.types import UIUserSettings
from passbook.flows.models import ConfigurableStage, Stage


class OTPStaticStage(ConfigurableStage, Stage):
    """Generate static tokens for the user as a backup."""

    token_count = models.IntegerField(default=6)

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.stages.otp_static.api import OTPStaticStageSerializer

        return OTPStaticStageSerializer

    @property
    def type(self) -> Type[View]:
        from passbook.stages.otp_static.stage import OTPStaticStageView

        return OTPStaticStageView

    @property
    def form(self) -> Type[ModelForm]:
        from passbook.stages.otp_static.forms import OTPStaticStageForm

        return OTPStaticStageForm

    @property
    def ui_user_settings(self) -> Optional[UIUserSettings]:
        return UIUserSettings(
            name="Static OTP",
            url=reverse(
                "passbook_stages_otp_static:user-settings",
                kwargs={"stage_uuid": self.stage_uuid},
            ),
        )

    def __str__(self) -> str:
        return f"OTP Static Stage {self.name}"

    class Meta:

        verbose_name = _("OTP Static Setup Stage")
        verbose_name_plural = _("OTP Static Setup Stages")
