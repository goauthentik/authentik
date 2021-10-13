"""OTP Time-based models"""
from typing import Optional, Type

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from django_otp.models import SideChannelDevice
from requests.exceptions import RequestException
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger

from authentik.core.types import UserSettingSerializer
from authentik.flows.models import ConfigurableStage, Stage
from authentik.lib.utils.http import get_http_session

LOGGER = get_logger()


class SMSProviders(models.TextChoices):
    """Supported SMS Providers"""

    TWILIO = "twilio"
    GENERIC = "generic"


class SMSAuthTypes(models.TextChoices):
    """Supported SMS Auth Types"""
    BEARER = "bearer"
    BASIC = "basic"


class AuthenticatorSMSStage(ConfigurableStage, Stage):
    """Use SMS-based TOTP instead of authenticator-based."""

    provider = models.TextField(choices=SMSProviders.choices)

    from_number = models.TextField()

    account_sid = models.TextField()
    auth = models.TextField()
    auth_password = models.TextField(null=True)
    auth_type = models.TextField(choices=SMSAuthTypes.choices, null=True)

    def send(self, token: str, device: "SMSDevice"):
        """Send message via selected provider"""
        if self.provider == SMSProviders.TWILIO:
            return self.send_twilio(token, device)
        if self.provider == SMSProviders.GENERIC:
            return self.send_generic(token, device)
        raise ValueError(f"invalid provider {self.provider}")

    def send_twilio(self, token: str, device: "SMSDevice"):
        """send sms via twilio provider"""
        response = get_http_session().post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
            data={
                "From": self.from_number,
                "To": device.phone_number,
                "Body": token,
            },
            auth=(self.account_sid, self.auth),
        )
        LOGGER.debug("Sent SMS", to=device.phone_number)
        try:
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Error sending token by Twilio SMS", exc=exc, body=response.text)
            if response.status_code == 400:
                raise ValidationError(response.json().get("message"))
            raise

        if "sid" not in response.json():
            message = response.json().get("message")
            LOGGER.warning("Error sending token by Twilio SMS", message=message)
            raise Exception(message)

    def send_generic(self, token: str, device: "SMSDevice"):
        """Send SMS via outside API"""
        from_number = ""

        if self.from_number is not None:
            from_number += self.from_number
        else:
            from_number += "None"

        data = {
            "From": from_number,
            "To": device.phone_number,
            "Body": token,
        }

        if self.auth_type == SMSAuthTypes.BEARER:
            response = get_http_session().post(
                f"{self.account_sid}",
                json=data,
                headers={
                    "Authorization": f"Bearer {self.auth}"
                },
            )

        elif self.auth_type == SMSAuthTypes.BASIC:
            response = get_http_session().post(
                f"{self.account_sid}",
                json=data,
                auth=(self.auth, self.auth_password),
            )
        else:
            raise

        LOGGER.debug("Sent SMS", to=device.phone_number)
        try:
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Error sending token by generic SMS", exc=exc)
            if response.status_code == 400:
                raise ValidationError(response.json().get("message"))
            if response.status_code == 521:
                LOGGER.debug("Cloudflare reported that origin web server is down, unable to connect, 521")
                raise ValidationError("Cloudflare reported that origin web server is down, unable to connect, 521")
            if response.status_code == 522:
                LOGGER.debug("Cloudflare reported connection timed out, 522")
                raise ValidationError("Cloudflare reported connection timed out, 522")
            if response.status_code == 523:
                LOGGER.debug("Cloudflare reported that origin is unreachable, 523")
                raise ValidationError("Cloudflare reported that origin is unreachable, 523")
            if response.status_code == 524:
                LOGGER.debug("Cloudflare was able to connect to origin, but it did not provide response "
                             "in timely fashion, 524")
                raise ValidationError("Cloudflare was able to connect to origin, but it did not provide response "
                                      "in timely fashion, 524")
            if response.status_code == 525:
                LOGGER.debug("Cloudflare reported an SSL handshake failure, 525")
                raise ValidationError("Cloudflare reported an SSL handshake failure, 525")
            if response.status_code == 526:
                LOGGER.debug("Cloudflare reported an invalid SSL certificate error, 526")
                raise ValidationError("Cloudflare reported an error, 526")
            raise

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.stages.authenticator_sms.api import AuthenticatorSMSStageSerializer

        return AuthenticatorSMSStageSerializer

    @property
    def type(self) -> Type[View]:
        from authentik.stages.authenticator_sms.stage import AuthenticatorSMSStageView

        return AuthenticatorSMSStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-sms-form"

    @property
    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-sms",
            }
        )

    def __str__(self) -> str:
        return f"SMS Authenticator Setup Stage {self.name}"

    class Meta:

        verbose_name = _("SMS Authenticator Setup Stage")
        verbose_name_plural = _("SMS Authenticator Setup Stages")


class SMSDevice(SideChannelDevice):
    """SMS Device"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorSMSStage, on_delete=models.CASCADE)

    phone_number = models.TextField()

    def __str__(self):
        return self.name or str(self.user)

    class Meta:
        verbose_name = _("SMS Device")
        verbose_name_plural = _("SMS Devices")
