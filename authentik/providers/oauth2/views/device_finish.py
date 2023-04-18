"""Device flow finish stage"""
from django.http import HttpResponse
from rest_framework.fields import CharField

from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import FlowPlan
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.providers.oauth2.models import DeviceToken

PLAN_CONTEXT_DEVICE = "goauthentik.io/providers/oauth2/device"


class OAuthDeviceCodeFinishChallenge(Challenge):
    """Final challenge after user enters their code"""

    component = CharField(default="ak-provider-oauth2-device-code-finish")


class OAuthDeviceCodeFinishChallengeResponse(ChallengeResponse):
    """Response that device has been authenticated and tab can be closed"""

    component = CharField(default="ak-provider-oauth2-device-code-finish")


class OAuthDeviceCodeFinishStage(ChallengeStageView):
    """Stage show at the end of a device flow"""

    response_class = OAuthDeviceCodeFinishChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
        token: DeviceToken = plan.context[PLAN_CONTEXT_DEVICE]
        # As we're required to be authenticated by now, we can rely on
        # request.user
        token.user = self.request.user
        token.save()
        return OAuthDeviceCodeFinishChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "component": "ak-provider-oauth2-device-code-finish",
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        self.executor.stage_ok()
