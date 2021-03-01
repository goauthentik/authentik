"""write stage models"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class UserWriteStage(Stage):
    """Writes currently pending data into the pending user, or if no user exists,
    creates a new user with the data."""

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.user_write.api import UserWriteStageSerializer

        return UserWriteStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.user_write.stage import UserWriteStageView

        return UserWriteStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.user_write.forms import UserWriteStageForm

        return UserWriteStageForm

    class Meta:

        verbose_name = _("User Write Stage")
        verbose_name_plural = _("User Write Stages")
