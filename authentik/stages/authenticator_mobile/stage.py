"""Mobile stage"""
from django.http import HttpResponse
from django.utils.timezone import now
from rest_framework.fields import CharField

from authentik.events.models import Event, EventAction
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_mobile.models import AuthenticatorMobileStage

SESSION_KEY_MOBILE_ENROLL = "authentik/stages/authenticator_mobile/enroll"


class AuthenticatorMobileChallenge(WithUserInfoChallenge):
    """Mobile Challenge"""

    authentik_url = CharField(required=True)
    stage_uuid = CharField(required=True)
    component = CharField(default="ak-stage-authenticator-mobile")


class AuthenticatorMobileChallengeResponse(ChallengeResponse):
    """Pseudo class for mobile response"""

    component = CharField(default="ak-stage-authenticator-mobile")


class AuthenticatorMobileStageView(ChallengeStageView):
    """Mobile stage"""

    response_class = AuthenticatorMobileChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        stage: AuthenticatorMobileStage = self.executor.current_stage
        return AuthenticatorMobileChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "authentik_url": self.request.get_host(),
                "stage_uuid": str(stage.stage_uuid),
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()
