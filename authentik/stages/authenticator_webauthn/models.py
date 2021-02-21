"""WebAuthn stage"""
from typing import Optional, Type

from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ModelForm
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import ConfigurableStage, Stage


class AuthenticateWebAuthnStage(ConfigurableStage, Stage):
    """WebAuthn stage"""

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_webauthn.api import (
            AuthenticateWebAuthnStageSerializer,
        )

        return AuthenticateWebAuthnStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.authenticator_webauthn.stage import (
            AuthenticatorWebAuthnStageView,
        )

        return AuthenticatorWebAuthnStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.authenticator_webauthn.forms import (
            AuthenticateWebAuthnStageForm,
        )

        return AuthenticateWebAuthnStageForm

    @property
    def ui_user_settings(self) -> Optional[str]:
        return reverse(
            "authentik_stages_authenticator_webauthn:user-settings",
            kwargs={"stage_uuid": self.stage_uuid},
        )

    def __str__(self) -> str:
        return f"WebAuthn Authenticator Setup Stage {self.name}"

    class Meta:

        verbose_name = _("WebAuthn Authenticator Setup Stage")
        verbose_name_plural = _("WebAuthn Authenticator Setup Stages")


class WebAuthnDevice(models.Model):
    """WebAuthn Device for a single user"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    name = models.TextField(max_length=200)
    credential_id = models.CharField(max_length=300, unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    rp_id = models.CharField(max_length=253)

    created_on = models.DateTimeField(auto_now_add=True)
    last_used_on = models.DateTimeField(default=now)

    def set_sign_count(self, sign_count: int) -> None:
        """Set the sign_count and update the last_used_on datetime."""
        self.sign_count = sign_count
        self.last_used_on = now()
        self.save()

    def __str__(self):
        return self.name or str(self.user)
