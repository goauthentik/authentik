"""Duo stage"""
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from duo_client.admin import Admin
from duo_client.auth import Auth
from rest_framework.serializers import BaseSerializer, Serializer

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.models import SerializerModel
from authentik.lib.utils.http import authentik_user_agent
from authentik.stages.authenticator.models import Device


class AuthenticatorDuoStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Setup Duo authenticator devices"""

    api_hostname = models.TextField()

    client_id = models.TextField()
    client_secret = models.TextField()

    admin_integration_key = models.TextField(blank=True, default="")
    admin_secret_key = models.TextField(blank=True, default="")

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_duo.api import AuthenticatorDuoStageSerializer

        return AuthenticatorDuoStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_duo.stage import AuthenticatorDuoStageView

        return AuthenticatorDuoStageView

    def auth_client(self) -> Auth:
        """Get an API Client to talk to duo"""
        return Auth(
            self.client_id,
            self.client_secret,
            self.api_hostname,
            user_agent=authentik_user_agent(),
        )

    def admin_client(self) -> Admin:
        """Get an API Client to talk to duo"""
        if self.admin_integration_key == "" or self.admin_secret_key == "":  # nosec
            raise ValueError("Admin credentials not configured")
        client = Admin(
            self.admin_integration_key,
            self.admin_secret_key,
            self.api_hostname,
            user_agent=authentik_user_agent(),
        )
        return client

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-duo-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-duo",
            }
        )

    def __str__(self) -> str:
        return f"Duo Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("Duo Authenticator Setup Stage")
        verbose_name_plural = _("Duo Authenticator Setup Stages")


class DuoDevice(SerializerModel, Device):
    """Duo Device for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorDuoStage, on_delete=models.CASCADE)
    duo_user_id = models.TextField()
    last_t = models.DateTimeField(auto_now=True)

    @property
    def serializer(self) -> Serializer:
        from authentik.stages.authenticator_duo.api import DuoDeviceSerializer

        return DuoDeviceSerializer

    def __str__(self):
        return str(self.name) or str(self.user)

    class Meta:
        verbose_name = _("Duo Device")
        verbose_name_plural = _("Duo Devices")
