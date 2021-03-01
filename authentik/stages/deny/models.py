"""deny stage models"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class DenyStage(Stage):
    """Cancells the current flow."""

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.deny.api import DenyStageSerializer

        return DenyStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.deny.stage import DenyStageView

        return DenyStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.deny.forms import DenyStageForm

        return DenyStageForm

    class Meta:

        verbose_name = _("Deny Stage")
        verbose_name_plural = _("Deny Stages")
