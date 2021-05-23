"""Duo stage"""
from typing import Optional, Type

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from django_otp.models import Device
from duo_client.auth import Auth
from rest_framework.serializers import BaseSerializer

from authentik import __version__
from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, Stage


class AuthenticatorDuoStage(ConfigurableStage, Stage):
    """Duo stage"""

    client_id = models.TextField()
    client_secret = models.TextField()
    api_hostname = models.TextField()

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_duo.api import (
            AuthenticatorDuoStageSerializer,
        )

        return AuthenticatorDuoStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.authenticator_duo.stage import AuthenticatorDuoStageView

        return AuthenticatorDuoStageView

    _client: Optional[Auth] = None

    @property
    def client(self) -> Auth:
        if not self._client:
            self._client = Auth(
                self.client_id,
                self.client_secret,
                self.api_hostname,
                user_agent=f"authentik {__version__}",
            )
            try:
                self._client.ping()
            except RuntimeError:
                # Either allow login without 2FA, or abort the login process
                # TODO: Define action when duo unavailable
                raise
        return self._client

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-duo-form"

    @property
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

    duo_user_id = models.TextField()

    def __str__(self):
        return self.name or str(self.user)

    class Meta:

        verbose_name = _("Duo Device")
        verbose_name_plural = _("Duo Devices")
