"""OTP Time-based models"""
import time
from base64 import b32encode
from binascii import unhexlify
from typing import Optional
from urllib.parse import quote, urlencode

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.serializers import BaseSerializer

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.models import SerializerModel
from authentik.stages.authenticator.models import Device, ThrottlingMixin
from authentik.stages.authenticator.oath import TOTP
from authentik.stages.authenticator.util import hex_validator, random_hex


class TOTPDigits(models.IntegerChoices):
    """OTP Time Digits"""

    SIX = 6, _("6 digits, widely compatible")
    EIGHT = 8, _("8 digits, not compatible with apps like Google Authenticator")


class AuthenticatorTOTPStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Enroll a user's device into Time-based OTP."""

    digits = models.IntegerField(choices=TOTPDigits.choices)

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_totp.api import AuthenticatorTOTPStageSerializer

        return AuthenticatorTOTPStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_totp.stage import AuthenticatorTOTPStageView

        return AuthenticatorTOTPStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-totp-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-totp",
            }
        )

    def __str__(self) -> str:
        return f"TOTP Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("TOTP Authenticator Setup Stage")
        verbose_name_plural = _("TOTP Authenticator Setup Stages")


def default_key():
    """Default TOTP Device key"""
    return random_hex(20)


def key_validator(value):
    """Validate totp key"""
    return hex_validator()(value)


class TOTPDevice(SerializerModel, ThrottlingMixin, Device):
    """
    A generic TOTP :class:`~authentik.stages.authenticator.models.Device`. The model fields mostly
    correspond to the arguments to :func:`authentik.stages.authenticator.oath.totp`. They all have
    sensible defaults, including the key, which is randomly generated.

    .. attribute:: key

        *CharField*: A hex-encoded secret key of up to 40 bytes. (Default: 20
        random bytes)

    .. attribute:: step

        *PositiveSmallIntegerField*: The time step in seconds. (Default: 30)

    .. attribute:: t0

        *BigIntegerField*: The Unix time at which to begin counting steps.
        (Default: 0)

    .. attribute:: digits

        *PositiveSmallIntegerField*: The number of digits to expect in a token
        (6 or 8).  (Default: 6)

    .. attribute:: tolerance

        *PositiveSmallIntegerField*: The number of time steps in the past or
        future to allow. For example, if this is 1, we'll accept any of three
        tokens: the current one, the previous one, and the next one. (Default:
        1)

    .. attribute:: drift

        *SmallIntegerField*: The number of time steps the prover is known to
        deviate from our clock.  If :setting:`OTP_TOTP_SYNC` is ``True``, we'll
        update this any time we match a token that is not the current one.
        (Default: 0)

    .. attribute:: last_t

        *BigIntegerField*: The time step of the last verified token. To avoid
        verifying the same token twice, this will be updated on each successful
        verification. Only tokens at a higher time step will be verified
        subsequently. (Default: -1)

    """

    key = models.CharField(
        max_length=80,
        validators=[key_validator],
        default=default_key,
        help_text="A hex-encoded secret key of up to 40 bytes.",
    )
    step = models.PositiveSmallIntegerField(default=30, help_text="The time step in seconds.")
    t0 = models.BigIntegerField(
        default=0, help_text="The Unix time at which to begin counting steps."
    )
    digits = models.PositiveSmallIntegerField(
        choices=[(6, 6), (8, 8)],
        default=6,
        help_text="The number of digits to expect in a token.",
    )
    tolerance = models.PositiveSmallIntegerField(
        default=1, help_text="The number of time steps in the past or future to allow."
    )
    drift = models.SmallIntegerField(
        default=0,
        help_text="The number of time steps the prover is known to deviate from our clock.",
    )
    last_t = models.BigIntegerField(
        default=-1,
        help_text=(
            "The t value of the latest verified token. "
            "The next token must be at a higher time step."
        ),
    )

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_totp.api import TOTPDeviceSerializer

        return TOTPDeviceSerializer

    @property
    def bin_key(self):
        """
        The secret key as a binary string.
        """
        return unhexlify(self.key.encode())

    def verify_token(self, token):
        otp_totp_sync = getattr(settings, "OTP_TOTP_SYNC", True)

        verify_allowed, _ = self.verify_is_allowed()
        if not verify_allowed:
            return False

        try:
            token = int(token)
        except ValueError:
            verified = False
        else:
            key = self.bin_key

            totp = TOTP(key, self.step, self.t0, self.digits, self.drift)
            totp.time = time.time()

            verified = totp.verify(token, self.tolerance, self.last_t + 1)
            if verified:
                self.last_t = totp.t()
                if otp_totp_sync:
                    self.drift = totp.drift
                self.throttle_reset(commit=False)
                self.save()

        if not verified:
            self.throttle_increment(commit=True)

        return verified

    def get_throttle_factor(self):
        return getattr(settings, "OTP_TOTP_THROTTLE_FACTOR", 1)

    @property
    def config_url(self):
        """
        A URL for configuring Google Authenticator or similar.

        See https://github.com/google/google-authenticator/wiki/Key-Uri-Format.
        The issuer is taken from :setting:`OTP_TOTP_ISSUER`, if available.
        The image (for e.g. FreeOTP) is taken from :setting:`OTP_TOTP_IMAGE`, if available.

        """
        label = str(self.user.username)
        params = {
            "secret": b32encode(self.bin_key),
            "algorithm": "SHA1",
            "digits": self.digits,
            "period": self.step,
        }
        urlencoded_params = urlencode(params)

        issuer = self._read_str_from_settings("OTP_TOTP_ISSUER")
        if issuer:
            issuer = issuer.replace(":", "")
            label = "{}:{}".format(issuer, label)
            urlencoded_params += "&issuer={}".format(
                quote(issuer)
            )  # encode issuer as per RFC 3986, not quote_plus

        image = self._read_str_from_settings("OTP_TOTP_IMAGE")
        if image:
            urlencoded_params += "&image={}".format(quote(image, safe=":/"))

        url = "otpauth://totp/{}?{}".format(quote(label), urlencoded_params)

        return url

    def _read_str_from_settings(self, key):
        val = getattr(settings, key, None)
        if callable(val):
            val = val(self)
        if isinstance(val, str) and (val != ""):
            return val
        return None

    class Meta(Device.Meta):
        verbose_name = _("TOTP Device")
        verbose_name_plural = _("TOTP Devices")
