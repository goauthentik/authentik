"""delete stage models"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from passbook.flows.models import Stage


class UserDeleteStage(Stage):
    """Deletes the currently pending user without confirmation.
    Use with caution."""

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.stages.user_delete.api import UserDeleteStageSerializer

        return UserDeleteStageSerializer

    def type(self) -> Type[View]:
        from passbook.stages.user_delete.stage import UserDeleteStageView

        return UserDeleteStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.user_delete.forms import UserDeleteStageForm

        return UserDeleteStageForm

    def __str__(self):
        return f"User Delete Stage {self.name}"

    class Meta:

        verbose_name = _("User Delete Stage")
        verbose_name_plural = _("User Delete Stages")
