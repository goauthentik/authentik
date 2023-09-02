from base64 import b32encode
from binascii import unhexlify
from urllib.parse import quote, urlencode

from django.conf import settings
from django.db import models

from authentik.stages.authenticator.models import Device, ThrottlingMixin
from authentik.stages.authenticator.oath import hotp
from authentik.stages.authenticator.util import hex_validator, random_hex


def default_key():
    return random_hex(20)


def key_validator(value):
    return hex_validator()(value)


class HOTPDevice(ThrottlingMixin, Device):
    """
    A generic HOTP :class:`~django_otp.models.Device`. The model fields mostly
    correspond to the arguments to :func:`django_otp.oath.hotp`. They all have
    sensible defaults, including the key, which is randomly generated.

    .. attribute:: key

        *CharField*: A hex-encoded secret key of up to 40 bytes. (Default: 20
        random bytes)

    .. attribute:: digits

        *PositiveSmallIntegerField*: The number of digits to expect from the
        token generator (6 or 8). (Default: 6)

    .. attribute:: tolerance

        *PositiveSmallIntegerField*: The number of missed tokens to tolerate.
        (Default: 5)

    .. attribute:: counter

        *BigIntegerField*: The next counter value to expect. (Initial: 0)

    """

    key = models.CharField(
        max_length=80,
        validators=[key_validator],
        default=default_key,
        help_text="A hex-encoded secret key of up to 40 bytes.",
    )
    digits = models.PositiveSmallIntegerField(
        choices=[(6, 6), (8, 8)],
        default=6,
        help_text="The number of digits to expect in a token.",
    )
    tolerance = models.PositiveSmallIntegerField(
        default=5, help_text="The number of missed tokens to tolerate."
    )
    counter = models.BigIntegerField(default=0, help_text="The next counter value to expect.")

    class Meta(Device.Meta):
        verbose_name = "HOTP device"

    @property
    def bin_key(self):
        """
        The secret key as a binary string.
        """
        return unhexlify(self.key.encode())

    def verify_token(self, token):
        verify_allowed, _ = self.verify_is_allowed()
        if not verify_allowed:
            return False

        try:
            token = int(token)
        except Exception:
            verified = False
        else:
            key = self.bin_key

            for counter in range(self.counter, self.counter + self.tolerance + 1):
                if hotp(key, counter, self.digits) == token:
                    verified = True
                    self.counter = counter + 1
                    self.throttle_reset(commit=False)
                    self.save()
                    break
            else:
                verified = False

        if not verified:
            self.throttle_increment(commit=True)

        return verified

    def get_throttle_factor(self):
        return getattr(settings, "OTP_HOTP_THROTTLE_FACTOR", 1)

    @property
    def config_url(self):
        """
        A URL for configuring Google Authenticator or similar.

        See https://github.com/google/google-authenticator/wiki/Key-Uri-Format.
        The issuer is taken from :setting:`OTP_HOTP_ISSUER`, if available.

        """
        label = self.user.get_username()
        params = {
            "secret": b32encode(self.bin_key),
            "algorithm": "SHA1",
            "digits": self.digits,
            "counter": self.counter,
        }
        urlencoded_params = urlencode(params)

        issuer = getattr(settings, "OTP_HOTP_ISSUER", None)
        if callable(issuer):
            issuer = issuer(self)
        if isinstance(issuer, str) and (issuer != ""):
            issuer = issuer.replace(":", "")
            label = "{}:{}".format(issuer, label)
            urlencoded_params += "&issuer={}".format(
                quote(issuer)
            )  # encode issuer as per RFC 3986, not quote_plus

        url = "otpauth://hotp/{}?{}".format(quote(label), urlencoded_params)

        return url
