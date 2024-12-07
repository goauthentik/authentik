"""authentik redirect stage"""

from django.http.response import HttpResponse
from rest_framework.fields import CharField
from structlog.stdlib import get_logger

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
)
from authentik.flows.models import (
    Flow,
)
from authentik.flows.stage import ChallengeStageView
from authentik.stages.redirect.models import RedirectStage

LOGGER = get_logger()
PLAN_CONTEXT_REDIRECT_TO_FLOW = "redirect_to_flow"


class RedirectChallenge(Challenge):
    """Redirect challenge"""

    component = CharField(default="ak-stage-redirect")
    name = CharField()
    to = CharField()


class RedirectChallengeResponse(ChallengeResponse):
    """Redirect challenge response"""

    component = CharField(default="ak-stage-redirect")


class RedirectStageView(ChallengeStageView):
    """Redirect stage for testing with multiple stages"""

    response_class = RedirectChallengeResponse

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()

    def get_challenge(self, *args, **kwargs) -> Challenge:
        current_stage: RedirectStage = self.executor.current_stage
        flow: Flow = (
            Flow.objects.filter(
                slug=self.executor.plan.context.get(PLAN_CONTEXT_REDIRECT_TO_FLOW, "")
            ).first()
            or current_stage.redirect_to_flow
        )

        redirect_to = self.executor.switch_flow_with_context(
            flow, keep_context=current_stage.keep_context
        )
        return RedirectChallenge(
            data={
                "name": self.executor.current_stage.name,
                "to": redirect_to,
            }
        )
