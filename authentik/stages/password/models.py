"""password stage models"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext
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
    """Prompt the user for their password, and validate it against the configured backends."""

    backends = ArrayField(
        models.TextField(choices=get_authentication_backends()),
        help_text=_("Selection of backends to test the password against."),
    )
    failed_attempts_before_cancel = models.IntegerField(
        default=5,
        help_text=_(
            "How many failed password attempts are allowed before the flow is canceled. "
            "This setting does not deactivate the user."
        ),
    )
    failed_attempts_before_lockout = models.PositiveIntegerField(
        default=0,
        help_text=_(
            "How many consecutive failed password attempts occur before password login is locked. "
            "Set to 0 to disable lockout."
        ),
    )
    show_last_attempt_warning = models.BooleanField(
        default=False,
        help_text=_("Show a warning when the user has one password attempt remaining."),
    )
    last_attempt_warning_message = models.TextField(
        blank=True,
        default="",
        help_text=_("Optional custom warning. Leave blank to use the default message."),
    )
    show_lockout_message = models.BooleanField(
        default=False,
        help_text=_("Show a message to the user when their account is locked out."),
    )
    lockout_message = models.TextField(
        blank=True,
        default="",
        help_text=_("Optional custom lockout message. Leave blank to use the default message."),
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

    def get_last_attempt_message(self, fallback: str) -> str:
        """Return the configured last-attempt warning or the existing authentication error."""
        if not self.show_last_attempt_warning:
            return fallback
        return self.last_attempt_warning_message or gettext(
            "You have one password attempt remaining before your account is locked out. "
            "If you have forgotten your password, please contact your administrator."
        )

    def get_lockout_message(self, fallback: str) -> str:
        """Return the configured lockout message or the existing authentication error."""
        if not self.show_lockout_message:
            return fallback
        return self.lockout_message or gettext(
            "Your account has been locked out due to too many failed attempts. "
            "Please contact your administrator."
        )

    class Meta:
        verbose_name = _("Password Stage")
        verbose_name_plural = _("Password Stages")
