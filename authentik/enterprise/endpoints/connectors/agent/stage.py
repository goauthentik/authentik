from django.http import HttpResponse
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    FrameChallenge,
    FrameChallengeResponse,
)
from authentik.flows.stage import ChallengeStageView
from authentik.lib.generators import generate_id

PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE = "goauthentik.io/endpoints/connectors/agent/challenge"


class AuthenticatorEndpointStageView(ChallengeStageView):
    """Endpoint stage"""

    response_class = FrameChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        challenge = generate_id()
        self.executor.plan.context[PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE] = challenge
        return FrameChallenge(
            data={
                "component": "xak-flow-frame",
                "url": self.request.build_absolute_uri(
                    reverse("authentik_endpoints_connectors_agent:apple-ssoext")
                    + "?"
                    + urlencode({"challenge": challenge})
                ),
                "loading_overlay": True,
                "loading_text": _("Verifying your browser..."),
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()
