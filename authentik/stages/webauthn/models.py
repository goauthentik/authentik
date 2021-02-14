"""WebAuthn stage"""
from typing import Type

from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ModelForm
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class WebAuthnStage(Stage):
    """WebAuthn stage"""

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.webauthn.api import WebAuthnStageSerializer

        return WebAuthnStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.webauthn.stage import WebAuthnStageView

        return WebAuthnStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.webauthn.forms import WebAuthnStageForm

        return WebAuthnStageForm

    def __str__(self) -> str:
        return f"WebAuthn Stage {self.name}"

    class Meta:

        verbose_name = _("WebAuthn Setup Stage")
        verbose_name_plural = _("WebAuthn Setup Stages")


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
