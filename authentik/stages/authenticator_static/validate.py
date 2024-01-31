from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.flows.challenge import Challenge, ChallengeTypes
from authentik.stages.authenticator.validate import (
    DeviceChallenge,
    DeviceChallengeResponse,
    DeviceValidator,
)
from authentik.stages.authenticator_static.models import StaticDevice


class StaticDeviceChallenge(DeviceChallenge):
    component = CharField(default="ak-stage-authenticator-validate-device-static")


class StaticDeviceChallengeResponse(DeviceChallengeResponse[StaticDevice]):
    component = CharField(default="ak-stage-authenticator-validate-device-static")
    code = CharField()

    def validate_code(self, code: str) -> str:
        if not self.device.verify_token(code):
            raise ValidationError("Invalid token")
        return code


class StaticDeviceValidator(DeviceValidator[StaticDevice]):
    response_class = StaticDeviceChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return StaticDeviceChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
            }
        )
