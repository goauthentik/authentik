from django.utils.translation import gettext_lazy as _

from authentik.core.models import User
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.stages.authenticator_validate.challenge.base import (
    DeviceChallenge,
    DeviceChallenger,
    DeviceIndependentValidationMixin,
)


class TOTPChallenger(DeviceIndependentValidationMixin, DeviceChallenger):

    device_class = TOTPDevice
    validation_error_message = _(
        "Invalid Token. " "Please ensure the time on your device is accurate and try again."
    )

    def make_device_challenges(self, user: User) -> list[DeviceChallenge]:
        if not TOTPDevice.objects.filter(user=user).exists():
            return []
        return [self._make_device_challenge(None, user, {})]

    def initiate(self, device_challenge: dict):
        pass
