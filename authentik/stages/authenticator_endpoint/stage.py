from django.http import HttpResponse
from django.urls import reverse

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    FrameChallenge,
    FrameChallengeResponse,
)
from authentik.flows.stage import ChallengeStageView


class AuthenticatorEndpointStageView(ChallengeStageView):
    """Endpoint stage"""

    response_class = FrameChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return FrameChallenge(
            data={
                "component": "xak-flow-frame",
                "url": self.request.build_absolute_uri(
                    reverse("authentik_stages_authenticator_endpoint:chrome")
                ),
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()
