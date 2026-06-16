from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.lib.utils.email import mask_email
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.authenticator_email.models import EmailDevice
from authentik.stages.authenticator_validate.challenge.base import (
    DeviceChallenge,
    DeviceChallenger,
    DeviceDependentValidationMixin,
)


class EmailChallenger(DeviceDependentValidationMixin, DeviceChallenger):

    device_class = EmailDevice

    def make_device_challenges(self, user: User) -> list[DeviceChallenge]:
        try:
            device = EmailDevice.objects.get(user=user)
        except EmailDevice.DoesNotExist:
            return []
        except EmailDevice.MultipleObjectsReturned:
            device = EmailDevice.objects.filter(user=user).latest("last_used")
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="User has multiple email devices registered for MFA",
                user=device.user,
            ).from_http(self.request, device.user)
        return [self._make_device_challenge(device, user, {"email": mask_email(device.email)})]

    def initiate(self, device_challenge: dict):
        device = EmailDevice.objects.get(pk=device_challenge["device_uid"])
        valid_secs = int(timedelta_from_string(device.stage.token_expiry).total_seconds())
        device.generate_token(valid_secs=valid_secs)
        device.stage.send(device)
