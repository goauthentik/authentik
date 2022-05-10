"""Duo stage"""
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from django_otp.models import Device
from duo_client.auth import Auth
from rest_framework.serializers import BaseSerializer

from authentik import __version__
from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, Stage


class AuthenticatorDuoStage(ConfigurableStage, Stage):
    """Setup Duo authenticator devices"""

    client_id = models.TextField()
    client_secret = models.TextField()
    api_hostname = models.TextField()

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_duo.api import AuthenticatorDuoStageSerializer

        return AuthenticatorDuoStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_duo.stage import AuthenticatorDuoStageView

        return AuthenticatorDuoStageView

    @property
    def client(self) -> Auth:
        """Get an API Client to talk to duo"""
        client = Auth(
            self.client_id,
            self.client_secret,
            self.api_hostname,
            user_agent=f"authentik {__version__}",
        )
        return client

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-duo-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-duo",
            }
        )

    def __str__(self) -> str:
        return f"Duo Authenticator Setup Stage {self.name}"

    class Meta:

        verbose_name = _("Duo Authenticator Setup Stage")
        verbose_name_plural = _("Duo Authenticator Setup Stages")


class DuoDevice(Device):
    """Duo Device for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorDuoStage, on_delete=models.CASCADE)
    duo_user_id = models.TextField()

    last_t = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or str(self.user)

    class Meta:

        verbose_name = _("Duo Device")
        verbose_name_plural = _("Duo Devices")
