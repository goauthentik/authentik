"""authentik multi-stage authentication engine"""
from django.http.response import HttpResponse

from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.stage import ChallengeStageView


class DummyChallenge(Challenge):
    """Dummy challenge"""


class DummyChallengeResponse(ChallengeResponse):
    """Dummy challenge response"""


class DummyStageView(ChallengeStageView):
    """Dummy stage for testing with multiple stages"""

    response_class = DummyChallengeResponse

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return DummyChallenge(
            data={
                "type": ChallengeTypes.native,
                "component": "",
                "title": self.executor.current_stage.name,
            }
        )
