"""Mobile stage"""
from django.http import HttpResponse
from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.stage import ChallengeStageView
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_mobile.models import MobileDevice, MobileDeviceToken

FLOW_PLAN_MOBILE_ENROLL_TOKEN = "authentik/stages/authenticator_mobile/enroll/token"  # nosec
FLOW_PLAN_MOBILE_ENROLL_DEVICE = "authentik/stages/authenticator_mobile/enroll/device"


class AuthenticatorMobilePayloadChallenge(PassiveSerializer):
    """Payload within the QR code given to the mobile app, hence the short variable names"""

    u = CharField(required=False, help_text="Server URL")
    s = CharField(required=False, help_text="Stage UUID")
    t = CharField(required=False, help_text="Initial Token")


class AuthenticatorMobileChallenge(WithUserInfoChallenge):
    """Mobile Challenge"""

    payload = AuthenticatorMobilePayloadChallenge(required=True)
    component = CharField(default="ak-stage-authenticator-mobile")


class AuthenticatorMobileChallengeResponse(ChallengeResponse):
    """Pseudo class for mobile response"""

    component = CharField(default="ak-stage-authenticator-mobile")


class AuthenticatorMobileStageView(ChallengeStageView):
    """Mobile stage"""

    response_class = AuthenticatorMobileChallengeResponse

    def prepare(self):
        """Prepare the token"""
        if FLOW_PLAN_MOBILE_ENROLL_TOKEN in self.executor.plan.context:
            return
        device = MobileDevice.objects.create(
            name=generate_id(),
            device_id=generate_id(),
            user=self.get_pending_user(),
            stage=self.executor.current_stage,
            confirmed=False,
        )
        token = MobileDeviceToken.objects.create(
            user=device.user,
            device=device,
        )
        self.executor.plan.context[FLOW_PLAN_MOBILE_ENROLL_TOKEN] = token
        self.executor.plan.context[FLOW_PLAN_MOBILE_ENROLL_DEVICE] = device

    def get_challenge(self, *args, **kwargs) -> Challenge:
        self.prepare()
        payload = AuthenticatorMobilePayloadChallenge(
            data={
                # TODO: use cloud gateway?
                "u": self.request.build_absolute_uri("/"),
                "s": str(self.executor.plan.context[FLOW_PLAN_MOBILE_ENROLL_DEVICE].pk),
                "t": self.executor.plan.context[FLOW_PLAN_MOBILE_ENROLL_TOKEN].token,
            }
        )
        payload.is_valid()
        return AuthenticatorMobileChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "payload": payload.validated_data,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        device: MobileDevice = self.executor.plan.context[FLOW_PLAN_MOBILE_ENROLL_DEVICE]
        device.refresh_from_db()
        if not device.confirmed:
            return self.challenge_invalid(response)
        return self.executor.stage_ok()
