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
from authentik.stages.authenticator_totp.models import TOTPDevice


class TOTPDeviceChallenge(DeviceChallenge):
    component = CharField(default="ak-stage-authenticator-validate-device-totp")


class TOTPDeviceChallengeResponse(DeviceChallengeResponse[TOTPDevice]):
    component = CharField(default="ak-stage-authenticator-validate-device-totp")
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


class TOTPDeviceValidator(DeviceValidator[TOTPDevice]):
    response_class = TOTPDeviceChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return TOTPDeviceChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
            }
        )
