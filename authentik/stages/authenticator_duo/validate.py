"""DUO device validator"""
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
from authentik.stages.authenticator.validate import (
    DeviceChallenge,
    DeviceChallengeResponse,
    DeviceValidator,
)
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice
from authentik.stages.authenticator_validate.models import DeviceClasses
from authentik.stages.authenticator_validate.stage import PLAN_CONTEXT_SELECTED_CHALLENGE


class DuoDeviceChallenge(DeviceChallenge):
    """Duo device challenge"""

    component = CharField(default="ak-stage-authenticator-validate-device-duo")

    duo_txn = CharField(allow_blank=True)


class DuoDeviceChallengeResponse(DeviceChallengeResponse[DuoDevice]):
    """Validate Duo device"""

    component = CharField(default="ak-stage-authenticator-validate-device-duo")

    def validate(self, attrs: dict):
        stage: AuthenticatorDuoStage = self.device.stage
        selected_challenge = self.stage.executor.plan.context.get(
            PLAN_CONTEXT_SELECTED_CHALLENGE, None
        )
        if not selected_challenge or not isinstance(selected_challenge, DuoDeviceChallenge):
            raise ValidationError("Invalid selected challenge")
        try:
            auth_status = stage.auth_client().auth_status(selected_challenge.data["duo_txn"])
        except RuntimeError:
            raise ValidationError("Failed to check Duo status")
        # {'result': 'allow', 'status': 'allow', 'status_msg': 'Success. Logging you in...'}
        if auth_status["success"] != "allow":
            self.logger.debug(
                "duo push response", result=auth_status["result"], msg=auth_status["status_msg"]
            )
            login_failed.send(
                sender=__name__,
                credentials={"username": self.device.user.username},
                request=self.request,
                stage=self.executor.current_stage,
                device_class=DeviceClasses.DUO.value,
                duo_response=auth_status,
            )
            raise ValidationError("Duo denied access", code="denied")
        return attrs


class DuoDeviceValidator(DeviceValidator[DuoDevice]):
    """Validate duo devices"""

    response_class = DuoDeviceChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return DuoDeviceChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "duo_txn": "",
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
                async_txn=True,
            )
            challenge.data["duo_txn"] = response["txid"]
            self.logger.info("Sent Duo push notification", stage=stage, response=response)
        except RuntimeError as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to DUO authenticate user: {str(exc)}",
                user=user,
            ).from_http(self.request, user)
            raise ValidationError("Duo denied access", code="denied")
        return challenge
