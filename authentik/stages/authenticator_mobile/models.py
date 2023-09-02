"""Mobile authenticator stage"""
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from django_otp.models import Device
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.models import ExpiringModel
from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.generators import generate_id
from authentik.lib.models import SerializerModel


def default_token_key():
    """Default token key"""
    return generate_id(40)


class AuthenticatorMobileStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Setup Mobile authenticator devices"""

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_mobile.api.stage import (
            AuthenticatorMobileStageSerializer,
        )

        return AuthenticatorMobileStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_mobile.stage import AuthenticatorMobileStageView

        return AuthenticatorMobileStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-mobile-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-mobile",
            }
        )

    def __str__(self) -> str:
        return f"Mobile Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("Mobile Authenticator Setup Stage")
        verbose_name_plural = _("Mobile Authenticator Setup Stages")


class MobileDevice(SerializerModel, Device):
    """Mobile authenticator for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorMobileStage, on_delete=models.CASCADE)

    device_id = models.TextField(unique=True)

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.authenticator_mobile.api.device import MobileDeviceSerializer

        return MobileDeviceSerializer

    def __str__(self):
        return str(self.name) or str(self.user)

    class Meta:
        verbose_name = _("Mobile Device")
        verbose_name_plural = _("Mobile Devices")


class MobileDeviceToken(ExpiringModel):
    """Mobile device token"""

    device = models.ForeignKey(MobileDevice, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    token = models.TextField(default=default_token_key)

    firebase_token = models.TextField(blank=True)
