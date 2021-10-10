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


class AuthenticatorSMSStage(ConfigurableStage, Stage):
    """Use SMS-based TOTP instead of authenticator-based."""

    provider = models.TextField(choices=SMSProviders.choices)

    from_number = models.TextField()

    twilio_account_sid = models.TextField()
    twilio_auth = models.TextField()

    def send(self, token: str, device: "SMSDevice"):
        """Send message via selected provider"""
        if self.provider == SMSProviders.TWILIO:
            return self.send_twilio(token, device)
        raise ValueError(f"invalid provider {self.provider}")

    def send_twilio(self, token: str, device: "SMSDevice"):
        """send sms via twilio provider"""
        response = get_http_session().post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json",
            data={
                "From": self.from_number,
                "To": device.phone_number,
                "Body": token,
            },
            auth=(self.twilio_account_sid, self.twilio_auth),
        )
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
