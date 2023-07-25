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
from authentik.stages.authenticator_mobile.models import AuthenticatorMobileStage, MobileDeviceToken

FLOW_PLAN_MOBILE_ENROLL = "authentik/stages/authenticator_mobile/enroll"


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
        if FLOW_PLAN_MOBILE_ENROLL in self.executor.plan.context:
            return
        token = MobileDeviceToken.objects.create(
            user=self.get_pending_user(),
        )
        self.executor.plan.context[FLOW_PLAN_MOBILE_ENROLL] = token

    def get_challenge(self, *args, **kwargs) -> Challenge:
        stage: AuthenticatorMobileStage = self.executor.current_stage
        self.prepare()
        payload = AuthenticatorMobilePayloadChallenge(
            data={
                # TODO: use cloud gateway?
                "u": self.request.build_absolute_uri("/"),
                "s": str(stage.stage_uuid),
                "t": self.executor.plan.context[FLOW_PLAN_MOBILE_ENROLL].token,
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
        return self.executor.stage_ok()
