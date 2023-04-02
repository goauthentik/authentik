"""Static Authenticator models"""
from typing import Optional

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage


class AuthenticatorStaticStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Generate static tokens for the user as a backup."""

    token_count = models.IntegerField(default=6)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_static.api import AuthenticatorStaticStageSerializer

        return AuthenticatorStaticStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_static.stage import AuthenticatorStaticStageView

        return AuthenticatorStaticStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-static-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-static",
            }
        )

    def __str__(self) -> str:
        return f"Static Authenticator Stage {self.name}"

    class Meta:
        verbose_name = _("Static Authenticator Stage")
        verbose_name_plural = _("Static Authenticator Stages")
