"""Authenticator Validation Stage"""
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import NotConfiguredAction, Stage


class AuthenticatorValidateStage(Stage):
    """Validate user's configured OTP Device."""

    not_configured_action = models.TextField(
        choices=NotConfiguredAction.choices, default=NotConfiguredAction.SKIP
    )

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_validate.api import (
            AuthenticatorValidateStageSerializer,
        )

        return AuthenticatorValidateStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.authenticator_validate.stage import (
            AuthenticatorValidateStageView,
        )

        return AuthenticatorValidateStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.authenticator_validate.forms import (
            AuthenticatorValidateStageForm,
        )

        return AuthenticatorValidateStageForm

    def __str__(self) -> str:
        return f"Authenticator Validation Stage {self.name}"

    class Meta:

        verbose_name = _("Authenticator Validation Stage")
        verbose_name_plural = _("Authenticator Validation Stages")
