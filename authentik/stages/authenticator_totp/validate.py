from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.flows.challenge import Challenge
from authentik.stages.authenticator.validate import (
    DeviceChallenge,
    DeviceChallengeResponse,
    DeviceValidator,
)
from authentik.stages.authenticator_totp.models import TOTPDevice


class TOTPDeviceChallenge(DeviceChallenge):
    component = CharField(default="ak-stage-authenticator-validate-device-totp")


class TOTPDeviceChallengeResponse(DeviceChallengeResponse[TOTPDevice]):
    component = CharField(default="ak-stage-authenticator-validate-device-totp")
    code = CharField()

    def validate_code(self, code: str) -> str:
        if not self.device.verify_token(code):
            raise ValidationError("Invalid token")
        return code


class TOTPDeviceValidator(DeviceValidator[TOTPDevice]):
    response_class = TOTPDeviceChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return TOTPDeviceChallenge()
