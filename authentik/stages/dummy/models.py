"""dummy stage models"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class DummyStage(Stage):
    """Used for debugging."""

    __debug_only__ = True

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.dummy.api import DummyStageSerializer

        return DummyStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.dummy.stage import DummyStageView

        return DummyStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.dummy.forms import DummyStageForm

        return DummyStageForm

    def __str__(self):
        return f"Dummy Stage {self.name}"

    class Meta:

        verbose_name = _("Dummy Stage")
        verbose_name_plural = _("Dummy Stages")
