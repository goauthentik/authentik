"""write stage models"""
from typing import Type

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class UserWriteStage(Stage):
    """Writes currently pending data into the pending user, or if no user exists,
    creates a new user with the data."""

    create_users_as_inactive = models.BooleanField(
        default=False,
        help_text=_("When set, newly created users are inactive and cannot login."),
    )

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.user_write.api import UserWriteStageSerializer

        return UserWriteStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.user_write.stage import UserWriteStageView

        return UserWriteStageView

    @property
    def component(self) -> str:
        return "ak-stage-user-write-form"

    class Meta:

        verbose_name = _("User Write Stage")
        verbose_name_plural = _("User Write Stages")
