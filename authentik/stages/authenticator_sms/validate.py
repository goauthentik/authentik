from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.flows.challenge import Challenge, ChallengeTypes
from authentik.stages.authenticator.models import VerifyNotAllowed
from authentik.stages.authenticator.validate import (
    DeviceChallenge,
    DeviceChallengeResponse,
    DeviceValidator,
)
from authentik.stages.authenticator_sms.models import SMSDevice


class SMSDeviceChallenge(DeviceChallenge):
    component = CharField(default="ak-stage-authenticator-validate-device-sms")

    number_preview = CharField()


class SMSDeviceChallengeResponse(DeviceChallengeResponse[SMSDevice]):
    component = CharField(default="ak-stage-authenticator-validate-device-sms")
    code = CharField()

    def validate_code(self, code: str) -> str:
        allowed, allowed_hint = self.device.verify_is_allowed()
        if not allowed:
            if allowed_hint["reason"] == VerifyNotAllowed.N_FAILED_ATTEMPTS:
                raise ValidationError(
                    _(
                        "Device blocked due to %(count)d failed attempts"
                        % {"count": allowed_hint["failure_count"]}
                    )
                )
            raise ValidationError(_("Device not allowed"))
        if not self.device.verify_token(code):
            raise ValidationError(_("Invalid token"))
        return code


class SMSDeviceValidator(DeviceValidator[SMSDevice]):
    response_class = SMSDeviceChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return SMSDeviceChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "number_preview": "+49*********13",  # TODO
            }
        )

    def device_allowed(self) -> bool:
        return super().device_allowed() and not self.device.is_hashed

    def select_challenge(self, challenge: SMSDeviceChallenge):
        self.device.generate_token()
        self.device.stage.send(self.device.token, self.device)
        return challenge
