"""SMS Authenticator models"""
from hashlib import sha256
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.views import View
from django_otp.models import SideChannelDevice
from requests.exceptions import RequestException
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BaseSerializer
from structlog.stdlib import get_logger
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from authentik.core.types import UserSettingSerializer
from authentik.events.models import Event, EventAction, NotificationWebhookMapping
from authentik.events.utils import sanitize_item
from authentik.flows.models import ConfigurableStage, FriendlyNamedStage, Stage
from authentik.lib.models import SerializerModel
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.http import get_http_session

LOGGER = get_logger()


class SMSProviders(models.TextChoices):
    """Supported SMS Providers"""

    TWILIO = "twilio"
    GENERIC = "generic"


class SMSAuthTypes(models.TextChoices):
    """Supported SMS Auth Types"""

    BASIC = "basic"
    BEARER = "bearer"


class AuthenticatorSMSStage(ConfigurableStage, FriendlyNamedStage, Stage):
    """Use SMS-based TOTP instead of authenticator-based."""

    provider = models.TextField(choices=SMSProviders.choices)

    from_number = models.TextField()

    account_sid = models.TextField()
    auth = models.TextField()
    auth_password = models.TextField(default="", blank=True)
    auth_type = models.TextField(choices=SMSAuthTypes.choices, default=SMSAuthTypes.BASIC)

    verify_only = models.BooleanField(
        default=False,
        help_text=_(
            "When enabled, the Phone number is only used during enrollment to verify the "
            "users authenticity. Only a hash of the phone number is saved to ensure it is "
            "not re-used in the future."
        ),
    )

    mapping = models.ForeignKey(
        NotificationWebhookMapping,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        help_text=_("Optionally modify the payload being sent to custom providers."),
    )

    def send(self, token: str, device: "SMSDevice"):
        """Send message via selected provider"""
        if self.provider == SMSProviders.TWILIO:
            return self.send_twilio(token, device)
        if self.provider == SMSProviders.GENERIC:
            return self.send_generic(token, device)
        raise ValueError(f"invalid provider {self.provider}")

    def get_message(self, token: str) -> str:
        """Get SMS message"""
        return _("Use this code to authenticate in authentik: %(token)s" % {"token": token})

    def send_twilio(self, token: str, device: "SMSDevice"):
        """send sms via twilio provider"""
        client = Client(self.account_sid, self.auth)

        try:
            message = client.messages.create(
                to=device.phone_number, from_=self.from_number, body=str(self.get_message(token))
            )
            LOGGER.debug("Sent SMS", to=device, message=message.sid)
        except TwilioRestException as exc:
            LOGGER.warning("Error sending token by Twilio SMS", exc=exc, msg=exc.msg)
            raise ValidationError(exc.msg)

    def send_generic(self, token: str, device: "SMSDevice"):
        """Send SMS via outside API"""
        payload = {
            "From": self.from_number,
            "To": device.phone_number,
            "Body": token,
            "Message": str(self.get_message(token)),
        }

        if self.mapping:
            payload = sanitize_item(
                self.mapping.evaluate(
                    user=device.user,
                    request=None,
                    device=device,
                    token=token,
                    stage=self,
                )
            )

        if self.auth_type == SMSAuthTypes.BEARER:
            response = get_http_session().post(
                self.account_sid,
                json=payload,
                headers={"Authorization": f"Bearer {self.auth}"},
            )
        elif self.auth_type == SMSAuthTypes.BASIC:
            response = get_http_session().post(
                self.account_sid,
                json=payload,
                auth=(self.auth, self.auth_password),
            )
        else:
            raise ValueError(f"Invalid Auth type '{self.auth_type}'")

        LOGGER.debug("Sent SMS", to=device.phone_number)
        try:
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning(
                "Error sending token by generic SMS",
                exc=exc,
                status=response.status_code,
                body=response.text[:100],
            )
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="Error sending SMS",
                exc=exception_to_string(exc),
                status_code=response.status_code,
                body=response.text,
            ).set_user(device.user).save()
            if response.status_code >= 400:
                raise ValidationError(response.text)
            raise

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_sms.api import AuthenticatorSMSStageSerializer

        return AuthenticatorSMSStageSerializer

    @property
    def type(self) -> type[View]:
        from authentik.stages.authenticator_sms.stage import AuthenticatorSMSStageView

        return AuthenticatorSMSStageView

    @property
    def component(self) -> str:
        return "ak-stage-authenticator-sms-form"

    def ui_user_settings(self) -> Optional[UserSettingSerializer]:
        return UserSettingSerializer(
            data={
                "title": self.friendly_name or str(self._meta.verbose_name),
                "component": "ak-user-settings-authenticator-sms",
            }
        )

    def __str__(self) -> str:
        return f"SMS Authenticator Setup Stage {self.name}"

    class Meta:
        verbose_name = _("SMS Authenticator Setup Stage")
        verbose_name_plural = _("SMS Authenticator Setup Stages")


def hash_phone_number(phone_number: str) -> str:
    """Hash phone number with prefix"""
    return "hash:" + sha256(phone_number.encode()).hexdigest()


class SMSDevice(SerializerModel, SideChannelDevice):
    """SMS Device"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    # Connect to the stage to when validating access we know the API Credentials
    stage = models.ForeignKey(AuthenticatorSMSStage, on_delete=models.CASCADE)

    phone_number = models.TextField()

    last_t = models.DateTimeField(auto_now=True)

    def set_hashed_number(self):
        """Set phone_number to hashed number"""
        self.phone_number = hash_phone_number(self.phone_number)

    @property
    def is_hashed(self) -> bool:
        """Check if the phone number is hashed"""
        return self.phone_number.startswith("hash:")

    @property
    def serializer(self) -> type[BaseSerializer]:
        from authentik.stages.authenticator_sms.api import SMSDeviceSerializer

        return SMSDeviceSerializer

    def verify_token(self, token):
        valid = super().verify_token(token)
        if valid:
            self.save()
        return valid

    def __str__(self):
        return str(self.name) or str(self.user)

    class Meta:
        verbose_name = _("SMS Device")
        verbose_name_plural = _("SMS Devices")
        unique_together = (("stage", "phone_number"),)
