from authentik.core.models import User
from authentik.stages.authenticator_static.models import StaticDevice
from authentik.stages.authenticator_validate.challenge.base import (
    DeviceChallenge,
    DeviceChallenger,
    DeviceIndependentValidationMixin,
)


class StaticChallenger(DeviceIndependentValidationMixin, DeviceChallenger):

    device_class = StaticDevice

    def make_device_challenges(self, user: User) -> list[DeviceChallenge]:
        if not StaticDevice.objects.filter(user=user).exists():
            return []
        return [self._make_device_challenge(None, user, {})]

    def initiate(self, device_challenge: dict):
        pass
