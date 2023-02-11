"""login stage models"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.models import Stage
from authentik.lib.utils.time import timedelta_string_validator


class UserLoginStage(Stage):
    """Attaches the currently pending user to the current session."""

    session_duration = models.TextField(
        default="seconds=0",
        validators=[timedelta_string_validator],
        help_text=_(
            "Determines how long a session lasts. Default of 0 means "
            "that the sessions lasts until the browser is closed. "
            "(Format: hours=-1;minutes=-2;seconds=-3)"
        ),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.user_login.api import UserLoginStageSerializer

        return UserLoginStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.user_login.stage import UserLoginStageView

        return UserLoginStageView

    @property
    def component(self) -> str:
        return "ak-stage-user-login-form"

    class Meta:
        verbose_name = _("User Login Stage")
        verbose_name_plural = _("User Login Stages")
