from urllib.parse import urlencode

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as __
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.challenge.base import (
    ChallengeValidationError,
    DeviceChallenge,
    DeviceChallenger,
)

LOGGER = get_logger()


class DuoChallenger(DeviceChallenger):

    device_class = DuoDevice

    def make_device_challenges(self, user: User) -> list[DeviceChallenge]:
        return [
            self._make_device_challenge(device, user, {})
            for device in DuoDevice.objects.filter(user=user)
        ]

    def initiate(self, device_challenge: dict):
        pass

    def validate(
        self, devices: QuerySet[DuoDevice], challenge: dict, challenge_response: str | dict
    ) -> DuoDevice:
        """Duo authentication"""
        device = get_object_or_404(devices, pk=challenge_response)
        stage: AuthenticatorDuoStage = device.stage

        # Get additional context for push
        pushinfo = {
            __("Domain"): self.request.get_host(),
        }

        if self.flow_context.application is not None:
            pushinfo[__("Application")] = self.flow_context.application.name

        try:
            response = stage.auth_client().auth(
                "auto",
                user_id=device.duo_user_id,
                ipaddr=ClientIPMiddleware.get_client_ip(self.request),
                type=__(
                    "{brand_name} Login request".format_map(
                        {
                            "brand_name": self.request.brand.branding_title,
                        }
                    )
                ),
                display_username=device.user.username,
                device="auto",
                pushinfo=urlencode(pushinfo),
            )
            # {'result': 'allow', 'status': 'allow', 'status_msg': 'Success. Logging you in...'}
            if response["result"] == "deny":
                LOGGER.debug(
                    "duo push response", result=response["result"], msg=response["status_msg"]
                )
                raise ChallengeValidationError(
                    "Duo denied access",
                    code="denied",
                    failure_context={"duo_response": response, "device": device},
                )
            return device
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to DUO authenticate user: {str(exc)}",
                user=device.user,
            ).from_http(self.request, device.user)
            raise ChallengeValidationError(
                "Duo denied access", code="denied", failure_context={"device": device}
            ) from exc
