"""Static Authenticator models"""
from typing import Optional, Type

from django.db import models
from django.forms import ModelForm
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.challenge import Challenge, ChallengeTypes
from authentik.flows.models import ConfigurableStage, Stage


class AuthenticatorStaticStage(ConfigurableStage, Stage):
    """Generate static tokens for the user as a backup."""

    token_count = models.IntegerField(default=6)

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_static.api import (
            AuthenticatorStaticStageSerializer,
        )

        return AuthenticatorStaticStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.authenticator_static.stage import (
            AuthenticatorStaticStageView,
        )

        return AuthenticatorStaticStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.authenticator_static.forms import (
            AuthenticatorStaticStageForm,
        )

        return AuthenticatorStaticStageForm

    @property
    def ui_user_settings(self) -> Optional[Challenge]:
        return Challenge(
            data={
                "type": ChallengeTypes.shell.value,
                "title": str(self._meta.verbose_name),
                "component": reverse(
                    "authentik_stages_authenticator_static:user-settings",
                    kwargs={"stage_uuid": self.stage_uuid},
                ),
            }
        )

    def __str__(self) -> str:
        return f"Static Authenticator Stage {self.name}"

    class Meta:

        verbose_name = _("Static Authenticator Stage")
        verbose_name_plural = _("Static Authenticator Stages")
