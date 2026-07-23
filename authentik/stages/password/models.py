"""Password stage and device models."""

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.hashers import (
    acheck_password,
    check_password,
    identify_hasher,
    is_password_usable,
    make_password,
)
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, Stage
from authentik.stages.authenticator.models import Device
from authentik.stages.password import (
    BACKEND_APP_PASSWORD,
    BACKEND_INBUILT,
    BACKEND_KERBEROS,
    BACKEND_LDAP,
)

DEFAULT_PASSWORD_STAGE_NAME = "default-authentication-password"


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
    """A user's local password authenticator."""

    is_mfa = False

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_device",
    )
    stage = models.ForeignKey(PasswordStage, on_delete=models.PROTECT)
    password = models.CharField(max_length=128)
    password_change_date = models.DateTimeField(default=now)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.password.api import PasswordDeviceSerializer

        return PasswordDeviceSerializer

    @classmethod
    def default_stage(cls) -> PasswordStage:
        """Return the stage which owns passwords created outside a flow."""
        return PasswordStage.objects.get(name=DEFAULT_PASSWORD_STAGE_NAME)

    @classmethod
    def for_user(cls, user) -> PasswordDevice:
        """Return the user's password device, creating it when necessary."""
        try:
            return user.password_device
        except cls.DoesNotExist:
            device, _ = cls.objects.get_or_create(
                user=user,
                defaults={
                    "name": "Password",
                    "stage": cls.default_stage(),
                    "password": make_password(None),
                },
            )
            user.password_device = device
            return device

    def set_password(self, raw_password: str | None) -> None:
        """Hash and store a new password on this device."""
        self.password = make_password(raw_password)
        self.password_change_date = now()

    def set_password_from_hash(self, password_hash: str) -> None:
        """Store an already-hashed password after validating its format."""
        self.validate_password_hash(password_hash)
        self.password = password_hash
        self.password_change_date = now()

    @staticmethod
    def validate_password_hash(password_hash: str) -> None:
        """Validate that the value is a recognized Django password hash."""
        identify_hasher(password_hash)

    def check_password(self, raw_password: str) -> bool:
        """Check a raw password and persist transparent hash upgrades."""

        def setter(password: str) -> None:
            self.password = make_password(password)
            self.save(update_fields=["password"])

        return check_password(raw_password, self.password, setter)

    async def acheck_password(self, raw_password: str) -> bool:
        """Asynchronously check a raw password and persist hash upgrades."""

        async def setter(password: str) -> None:
            self.password = await sync_to_async(make_password)(password)
            await self.asave(update_fields=["password"])

        return await acheck_password(raw_password, self.password, setter)

    def set_unusable_password(self) -> None:
        """Retain the device while preventing password authentication."""
        self.password = make_password(None)

    def has_usable_password(self) -> bool:
        """Return whether this device contains a usable password hash."""
        return is_password_usable(self.password)

    class Meta(Device.Meta):
        verbose_name = _("Password Device")
        verbose_name_plural = _("Password Devices")
