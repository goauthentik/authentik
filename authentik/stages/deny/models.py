"""deny stage models"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class DenyStage(Stage):
    """Cancels the current flow."""

    deny_message = models.TextField(blank=True, default="")

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.deny.api import DenyStageSerializer

        return DenyStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.deny.stage import DenyStageView

        return DenyStageView

    @property
    def component(self) -> str:
        return "ak-stage-deny-form"

    class Meta:
        verbose_name = _("Deny Stage")
        verbose_name_plural = _("Deny Stages")
