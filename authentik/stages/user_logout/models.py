"""logout stage models"""
from typing import Type

from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage


class UserLogoutStage(Stage):
    """Resets the users current session."""

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.user_logout.api import UserLogoutStageSerializer

        return UserLogoutStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.user_logout.stage import UserLogoutStageView

        return UserLogoutStageView

    @property
    def component(self) -> str:
        return "ak-stage-user-logout-form"

    class Meta:

        verbose_name = _("User Logout Stage")
        verbose_name_plural = _("User Logout Stages")
