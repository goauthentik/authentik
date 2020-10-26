"""login stage models"""
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from passbook.flows.models import Stage
from passbook.lib.utils.time import timedelta_string_validator


class UserLoginStage(Stage):
    """Attaches the currently pending user to the current session."""

    session_duration = models.TextField(
        default="seconds=-1",
        validators=[timedelta_string_validator],
        help_text=_(
            "Determines how long a session lasts. Default of -1 means "
            "that the sessions lasts until the browser is closed. "
            "(Format: hours=-1;minutes=-2;seconds=-3)"
        ),
    )

    @property
    def serializer(self) -> BaseSerializer:
        from passbook.stages.user_login.api import UserLoginStageSerializer

        return UserLoginStageSerializer

    @property
    def type(self) -> Type[View]:
        from passbook.stages.user_login.stage import UserLoginStageView

        return UserLoginStageView

    @property
    def form(self) -> Type[ModelForm]:
        from passbook.stages.user_login.forms import UserLoginStageForm

        return UserLoginStageForm

    def __str__(self):
        return f"User Login Stage {self.name}"

    class Meta:

        verbose_name = _("User Login Stage")
        verbose_name_plural = _("User Login Stages")
