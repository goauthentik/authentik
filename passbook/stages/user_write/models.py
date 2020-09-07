"""write stage models"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from passbook.flows.models import Stage


class UserWriteStage(Stage):
    """Writes currently pending data into the pending user, or if no user exists,
    creates a new user with the data."""

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.stages.user_write.api import UserWriteStageSerializer

        return UserWriteStageSerializer

    def type(self) -> Type[View]:
        from passbook.stages.user_write.stage import UserWriteStageView

        return UserWriteStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.user_write.forms import UserWriteStageForm

        return UserWriteStageForm

    def __str__(self):
        return f"User Write Stage {self.name}"

    class Meta:

        verbose_name = _("User Write Stage")
        verbose_name_plural = _("User Write Stages")
