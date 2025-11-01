from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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
                    reverse("authentik_endpoints_connectors_google_chrome:chrome")
                ),
                "loading_overlay": True,
                "loading_text": _("Verifying your browser..."),
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()
