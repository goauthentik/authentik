"""password stage models"""

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.models import User
from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, Stage
from authentik.stages.authenticator.models import Device
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
            "How many attempts a user has before the flow is canceled. "
            "This only cancels the flow, it does not lock the user's password."
        ),
    )
    failed_attempts_before_lockout = models.PositiveIntegerField(
        default=0,
        help_text=_(
            "How many consecutive failed attempts lock the user's password until an "
            "administrator unlocks it. Set to 0 to never lock."
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
        help_text=_("Show a message to the user when their password is locked."),
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
        """Return the configured last-attempt warning or the existing error."""
        if not self.show_last_attempt_warning:
            return fallback
        return self.last_attempt_warning_message or gettext(
            "You have one password attempt remaining before your password is locked. "
            "If you have forgotten your password, please contact your administrator."
        )

    def get_lockout_message(self, fallback: str) -> str:
        """Return the configured lockout message or the existing error."""
        if not self.show_lockout_message:
            return fallback
        return self.lockout_message or gettext(
            "Your password has been locked due to too many failed attempts. "
            "Please contact your administrator."
        )

    class Meta:
        verbose_name = _("Password Stage")
        verbose_name_plural = _("Password Stages")


class PasswordDevice(Device):
    """A user's password, stored as an authenticator device.

    A password is a knowledge factor rather than a second factor, so this device is kept
    out of MFA discovery, validation and the device APIs."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="password_device")
    password = models.CharField(max_length=128)
    password_change_date = models.DateTimeField(default=now)
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_at = models.DateTimeField(default=None, null=True)

    class Meta(Device.Meta):
        verbose_name = _("Password Device")
        verbose_name_plural = _("Password Devices")

    @property
    def locked(self) -> bool:
        """Whether this password currently refuses authentication."""
        return self.locked_at is not None

    def unlock(self):
        """Allow authentication again and forget earlier failures."""
        self.failed_attempts = 0
        self.locked_at = None
        self.save(update_fields=["failed_attempts", "locked_at"])
