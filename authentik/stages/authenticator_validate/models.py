"""Authenticator Validation Stage"""
from typing import Type

from django.contrib.postgres.fields.array import ArrayField
from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import NotConfiguredAction, Stage


class DeviceClasses(models.TextChoices):
    """Device classes this stage can validate"""

    # device class must match Device's class name so StaticDevice -> static
    STATIC = "static"
    TOTP = "totp", _("TOTP")
    WEBAUTHN = "webauthn", _("WebAuthn")


def default_device_classes() -> list:
    """By default, accept all device classes"""
    return [
        DeviceClasses.STATIC,
        DeviceClasses.TOTP,
        DeviceClasses.WEBAUTHN,
    ]


class AuthenticatorValidateStage(Stage):
    """Validate user's configured OTP Device."""

    not_configured_action = models.TextField(
        choices=NotConfiguredAction.choices, default=NotConfiguredAction.SKIP
    )

    device_classes = ArrayField(
        models.TextField(),
        help_text=_("Device classes which can be used to authenticate"),
        default=default_device_classes,
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

    class Meta:

        verbose_name = _("Authenticator Validation Stage")
        verbose_name_plural = _("Authenticator Validation Stages")
