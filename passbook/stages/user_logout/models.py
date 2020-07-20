"""logout stage models"""
from typing import Type

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views import View

from passbook.flows.models import Stage


class UserLogoutStage(Stage):
    """Resets the users current session."""

    def type(self) -> Type[View]:
        from passbook.stages.user_logout.stage import UserLogoutStageView

        return UserLogoutStageView

    def form(self) -> Type[ModelForm]:
        from passbook.stages.user_logout.forms import UserLogoutStageForm

        return UserLogoutStageForm

    def __str__(self):
        return f"User Logout Stage {self.name}"

    class Meta:

        verbose_name = _("User Logout Stage")
        verbose_name_plural = _("User Logout Stages")
