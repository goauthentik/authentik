"""passbook consent stage"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View

from passbook.flows.models import Stage


class ConsentStage(Stage):
    """Prompt the user for confirmation."""

    def type(self) -> Type[View]:
        from passbook.stages.consent.stage import ConsentStageView

        return ConsentStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.consent.forms import ConsentStageForm

        return ConsentStageForm

    def __str__(self):
        return f"Consent Stage {self.name}"

    class Meta:

        verbose_name = _("Consent Stage")
        verbose_name_plural = _("Consent Stages")
