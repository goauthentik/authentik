"""password stage models"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, Stage
from authentik.stages.password import (
    BACKEND_APP_PASSWORD,
    BACKEND_INBUILT,
    BACKEND_KERBEROS,
    BACKEND_LDAP,
)


def get_authentication_backends():
    """Return all available authentication backends as tuple set"""
    return [
        (
            BACKEND_INBUILT,
            _("User database + standard password"),
        ),
        (
            BACKEND_APP_PASSWORD,
            _("User database + app passwords"),
        ),
        (
            BACKEND_LDAP,
            _("User database + LDAP password"),
        ),
        (
            BACKEND_KERBEROS,
            _("User database + Kerberos password"),
        ),
    ]


class PasswordStage(ConfigurableStage, Stage):
    """Prompts the user for their password, and validates it against the configured backends."""

    backends = ArrayField(
        models.TextField(choices=get_authentication_backends()),
        help_text=_("Selection of backends to test the password against."),
    )
    failed_attempts_before_cancel = models.IntegerField(
        default=5,
        help_text=_(
            "How many attempts a user has before the flow is canceled. "
            "To lock the user out, use a reputation policy and a user_write stage."
        ),
    )
    allow_show_password = models.BooleanField(
        default=False,
        help_text=_(
            "When enabled, provides a 'show password' button with the password input field."
        ),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.password.api import PasswordStageSerializer

        return PasswordStageSerializer

    @property
    def view(self) -> type[View]:
        from authentik.stages.password.stage import PasswordStageView

        return PasswordStageView

    @property
    def component(self) -> str:
        return "ak-stage-password-form"

    def ui_user_settings(self) -> UserSettingSerializer | None:
        if not self.configure_flow:
            return None
        return UserSettingSerializer(
            data={
                "title": str(self._meta.verbose_name),
                "component": "ak-user-settings-password",
            }
        )

    class Meta:
        verbose_name = _("Password Stage")
        verbose_name_plural = _("Password Stages")
