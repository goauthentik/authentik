from authentik.core.models import User
from authentik.stages.authenticator_sms.models import SMSDevice
from authentik.stages.authenticator_validate.challenge.base import (
    DeviceChallenge,
    DeviceChallenger,
    DeviceDependentValidationMixin,
)


class SMSChallenger(DeviceDependentValidationMixin, DeviceChallenger):

    device_class = SMSDevice

    def get_allowed_devices(self, user):
        return [d for d in super().get_allowed_devices(user) if not d.is_hashed]

    def make_device_challenges(self, user: User) -> list[DeviceChallenge]:
        return [
            self._make_device_challenge(device, user, {})
            for device in SMSDevice.objects.filter(user=user)
            if not device.is_hashed
        ]

    def initiate(self, device_challenge: dict):
        device = SMSDevice.objects.get(pk=device_challenge["device_uid"])
        device.generate_token()
        device.stage.send(self.request, device.token, device)
