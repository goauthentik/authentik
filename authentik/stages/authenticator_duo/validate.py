from urllib.parse import urlencode

from django.utils.translation import gettext as __
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.core.models import Application
from authentik.core.signals import login_failed
from authentik.events.models import Event, EventAction
from authentik.flows.challenge import Challenge, ChallengeTypes
from authentik.flows.views.executor import SESSION_KEY_APPLICATION_PRE
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.authenticator.validate import DeviceChallenge, DeviceValidator
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.models import DeviceClasses


class DuoDeviceChallenge(DeviceChallenge):
    component = CharField(default="ak-stage-authenticator-validate-device-duo")


class DuoDeviceValidator(DeviceValidator[DuoDevice]):
    """Validate duo devices"""

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return DuoDeviceChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
            }
        )

    def select_challenge(self, challenge: DuoDeviceChallenge):
        user = self.get_pending_user()
        if self.device.user != user:
            self.logger.warning("device mismatch")
            raise ValidationError("Invalid device")
        stage: AuthenticatorDuoStage = self.device.stage

        # Get additional context for push
        pushinfo = {
            __("Domain"): self.request.get_host(),
        }
        if SESSION_KEY_APPLICATION_PRE in self.request.session:
            pushinfo[__("Application")] = self.request.session.get(
                SESSION_KEY_APPLICATION_PRE, Application()
            ).name

        try:
            response = stage.auth_client().auth(
                "auto",
                user_id=self.device.duo_user_id,
                ipaddr=ClientIPMiddleware.get_client_ip(self.request),
                type=__(
                    "%(brand_name)s Login request"
                    % {
                        "brand_name": self.request.brand.branding_title,
                    }
                ),
                display_username=user.username,
                device="auto",
                pushinfo=urlencode(pushinfo),
            )
            # {'result': 'allow', 'status': 'allow', 'status_msg': 'Success. Logging you in...'}
            if response["result"] == "deny":
                self.logger.debug(
                    "duo push response", result=response["result"], msg=response["status_msg"]
                )
                login_failed.send(
                    sender=__name__,
                    credentials={"username": user.username},
                    request=self.request,
                    stage=self.executor.current_stage,
                    device_class=DeviceClasses.DUO.value,
                    duo_response=response,
                )
                raise ValidationError("Duo denied access", code="denied")
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to DUO authenticate user: {str(exc)}",
                user=user,
            ).from_http(self.request, user)
            raise ValidationError("Duo denied access", code="denied")
