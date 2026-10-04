"""password stage models"""

from datetime import datetime

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.timezone import now
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


class PasswordDevice(Device):
    """A user's password, excluded from MFA discovery and validation."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="password_device")
    password = models.CharField(max_length=128)
    password_change_date = models.DateTimeField(default=now)

    @classmethod
    def save_password_hash(
        cls, user: User, password: str, changed_at: datetime, using: str
    ) -> PasswordDevice:
        """Persist only password fields, preserving other device state."""
        defaults = {"password": password, "password_change_date": changed_at}
        device, _ = cls.objects.using(using).update_or_create(
            user=user,
            defaults=defaults,
            create_defaults={"name": "Password", **defaults},
        )
        return device

    def check_password(self, raw_password: str) -> bool:
        """Upgrade outdated hashes without replacing a concurrently changed password."""

        def setter(raw_password):
            password = make_password(raw_password)
            if (
                type(self)
                .objects.filter(pk=self.pk, password=self.password)
                .update(password=password)
            ):
                self.password = password

        return check_password(raw_password, self.password, setter)

    def __str__(self):
        return str(self.name) or str(self.user_id)

    class Meta(Device.Meta):
        verbose_name = _("Password Device")
        verbose_name_plural = _("Password Devices")
        indexes = [models.Index(fields=["password_change_date"])]
