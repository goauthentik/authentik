"""password stage models"""
from typing import Optional, Type

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import ModelForm
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.flows.challenge import Challenge, ChallengeTypes
from authentik.flows.models import ConfigurableStage, Stage


class PasswordStage(ConfigurableStage, Stage):
    """Prompts the user for their password, and validates it against the configured backends."""

    backends = ArrayField(
        models.TextField(),
        help_text=_("Selection of backends to test the password against."),
    )
    failed_attempts_before_cancel = models.IntegerField(
        default=5,
        help_text=_(
            (
                "How many attempts a user has before the flow is canceled. "
                "To lock the user out, use a reputation policy and a user_write stage."
            )
        ),
    )

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.password.api import PasswordStageSerializer

        return PasswordStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.password.stage import PasswordStageView

        return PasswordStageView

    @property
    def form(self) -> Type[ModelForm]:
        from authentik.stages.password.forms import PasswordStageForm

        return PasswordStageForm

    @property
    def ui_user_settings(self) -> Optional[Challenge]:
        if not self.configure_flow:
            return None
        return Challenge(
            data={
                "type": ChallengeTypes.shell.value,
                "title": str(self._meta.verbose_name),
                "component": reverse(
                    "authentik_stages_password:user-settings",
                    kwargs={"stage_uuid": self.pk},
                ),
            }
        )

    class Meta:

        verbose_name = _("Password Stage")
        verbose_name_plural = _("Password Stages")
