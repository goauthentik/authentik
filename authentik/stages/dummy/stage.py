"""authentik multi-stage authentication engine"""

from django.http.response import HttpResponse
from rest_framework.fields import CharField

from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.stage import ChallengeStageView
from authentik.lib.sentry import SentryIgnoredException


class DummyChallenge(Challenge):
    """Dummy challenge"""

    component = CharField(default="ak-stage-dummy")
    name = CharField()


class DummyChallengeResponse(ChallengeResponse):
    """Dummy challenge response"""

    component = CharField(default="ak-stage-dummy")


class DummyStageView(ChallengeStageView):
    """Dummy stage for testing with multiple stages"""

    response_class = DummyChallengeResponse

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()

    def get_challenge(self, *args, **kwargs) -> Challenge:
        if self.executor.current_stage.throw_error:
            raise SentryIgnoredException("Test error")
        return DummyChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "title": self.executor.current_stage.name,
                "name": self.executor.current_stage.name,
            }
        )
