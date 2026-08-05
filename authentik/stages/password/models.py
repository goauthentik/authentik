"""password stage models"""

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.models import User
from authentik.core.types import UserSettingSerializer
from authentik.enterprise.license import LicenseKey
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
            "How many consecutive failed attempts lock the user's password, until an "
            "administrator unlocks it or the password is changed. Set to 0 to never lock. "
            "Requires an enterprise license."
        ),
    )
    allow_show_password = models.BooleanField(
        default=False,
        help_text=_(
            "When enabled, provides a 'show password' button with the password input field."
        ),
    )

    @property
    def lockout_limit(self) -> int:
        """Failed-attempt limit in force, or 0 when this stage never locks a password."""
        if not self.failed_attempts_before_lockout:
            return 0
        if not LicenseKey.cached_summary().status.is_valid:
            return 0
        return self.failed_attempts_before_lockout

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


class PasswordDevice(Device):
    """A user's password, stored as an authenticator device."""

    # A password is a knowledge factor rather than a second factor, so this device is kept
    # out of MFA discovery, validation and the device APIs.
    is_mfa = False

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="password_device")
    password = models.CharField(max_length=128)
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_at = models.DateTimeField(default=None, null=True)

    class Meta(Device.Meta):
        verbose_name = _("Password Device")
        verbose_name_plural = _("Password Devices")

    @property
    def locked(self) -> bool:
        """Whether this password currently refuses authentication."""
        return self.locked_at is not None

    @classmethod
    def register_failure(cls, user: User, limit: int) -> bool:
        """Count a failed attempt against `user`, locking their password at `limit` failures.

        Returns whether the password is locked afterwards. The row is held for the update so
        that attempts made in parallel cannot undercount their way past the limit.
        """
        with transaction.atomic():
            device = cls.objects.select_for_update().filter(user=user).first()
            if device is None:
                return False
            device.failed_attempts += 1
            if limit and device.failed_attempts >= limit:
                device.locked_at = device.locked_at or now()
            device.save(update_fields=["failed_attempts", "locked_at"])
            return device.locked

    def unlock(self):
        """Allow authentication again and forget earlier failures."""
        self.failed_attempts = 0
        self.locked_at = None
        self.save(update_fields=["failed_attempts", "locked_at"])
