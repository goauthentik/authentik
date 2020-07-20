"""login stage models"""
from typing import Type

from django.db import models
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View

from passbook.flows.models import Stage


class UserLoginStage(Stage):
    """Attaches the currently pending user to the current session."""

    session_duration = models.PositiveIntegerField(
        default=0,
        help_text=_(
            "Determines how long a session lasts, in seconds. Default of 0 means"
            " that the sessions lasts until the browser is closed."
        ),
    )

    def type(self) -> Type[View]:
        from passbook.stages.user_login.stage import UserLoginStageView

        return UserLoginStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.user_login.forms import UserLoginStageForm

        return UserLoginStageForm

    def __str__(self):
        return f"User Login Stage {self.name}"

    class Meta:

        verbose_name = _("User Login Stage")
        verbose_name_plural = _("User Login Stages")
