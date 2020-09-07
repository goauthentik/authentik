"""dummy stage models"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from passbook.flows.models import Stage


class DummyStage(Stage):
    """Used for debugging."""

    __debug_only__ = True

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.stages.dummy.api import DummyStageSerializer

        return DummyStageSerializer

    def type(self) -> Type[View]:
        from passbook.stages.dummy.stage import DummyStageView

        return DummyStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.dummy.forms import DummyStageForm

        return DummyStageForm

    def __str__(self):
        return f"Dummy Stage {self.name}"

    class Meta:

        verbose_name = _("Dummy Stage")
        verbose_name_plural = _("Dummy Stages")
