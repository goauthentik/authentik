"""Static Authenticator models"""
from base64 import b32encode
from os import urandom
from typing import Optional

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.models import SerializerModel
from authentik.stages.authenticator.models import Device, ThrottlingMixin


class AuthenticatorStaticStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Generate static tokens for the user as a backup."""

    token_count = models.PositiveIntegerField(default=6)
    token_length = models.PositiveIntegerField(default=12)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_static.api import AuthenticatorStaticStageSerializer

        return AuthenticatorStaticStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_static.stage import AuthenticatorStaticStageView

        return AuthenticatorStaticStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-static-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-static",
            }
        )

    def __str__(self) -> str:
        return f"Static Authenticator Stage {self.name}"

    class Meta:
        verbose_name = _("Static Authenticator Stage")
        verbose_name_plural = _("Static Authenticator Stages")


class StaticDevice(SerializerModel, ThrottlingMixin, Device):
    """
    A static :class:`~authentik.stages.authenticator.models.Device` simply consists of random
    tokens shared by the database and the user.

    These are frequently used as emergency tokens in case a user's normal
    device is lost or unavailable. They can be consumed in any order; each
    token will be removed from the database as soon as it is used.

    This model has no fields of its own, but serves as a container for
    :class:`StaticToken` objects.

    .. attribute:: token_set

        The RelatedManager for our tokens.

    """

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_static.api import StaticDeviceSerializer

        return StaticDeviceSerializer

    def get_throttle_factor(self):
        return getattr(settings, "OTP_STATIC_THROTTLE_FACTOR", 1)

    def verify_token(self, token):
        verify_allowed, _ = self.verify_is_allowed()
        if verify_allowed:
            match = self.token_set.filter(token=token).first()
            if match is not None:
                match.delete()
                self.throttle_reset()
            else:
                self.throttle_increment()
        else:
            match = None

        return match is not None

    class Meta(Device.Meta):
        verbose_name = _("Static Device")
        verbose_name_plural = _("Static Devices")


class StaticToken(models.Model):
    """
    A single token belonging to a :class:`StaticDevice`.

    .. attribute:: device

        *ForeignKey*: A foreign key to :class:`StaticDevice`.

    .. attribute:: token

        *CharField*: A random string up to 16 characters.
    """

    device = models.ForeignKey(StaticDevice, related_name="token_set", on_delete=models.CASCADE)
    token = models.CharField(max_length=16, db_index=True)

    @staticmethod
    def random_token():
        """
        Returns a new random string that can be used as a static token.

        :rtype: bytes

        """
        return b32encode(urandom(5)).decode("utf-8").lower()

    class Meta:
        verbose_name = _("Static Token")
        verbose_name_plural = _("Static Tokens")
