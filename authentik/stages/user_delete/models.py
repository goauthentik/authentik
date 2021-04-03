"""delete stage models"""
from typing import Type

from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class UserDeleteStage(Stage):
    """Deletes the currently pending user without confirmation.
    Use with caution."""

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.user_delete.api import UserDeleteStageSerializer

        return UserDeleteStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.user_delete.stage import UserDeleteStageView

        return UserDeleteStageView

    @property
    def component(self) -> str:
        return "ak-stage-user-delete-form"

    class Meta:

        verbose_name = _("User Delete Stage")
        verbose_name_plural = _("User Delete Stages")
