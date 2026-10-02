"""authentik multi-stage authentication engine"""

from typing import cast, Any

from django.http.response import HttpResponse
from rest_framework.fields import CharField

from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.stage import ChallengeStageView
from authentik.stages.message.models import MessageStage


class MessageChallenge(Challenge):
    """Message challenge"""

    component = CharField(default="ak-stage-message")
    name = CharField()
    title = CharField(required=False, allow_blank=True, default="")
    message = CharField()
    button_text = CharField(required=False, allow_blank=True, default="")


class MessageChallengeResponse(ChallengeResponse):
    """Message challenge response"""

    component = CharField(default="ak-stage-message")


class MessageStageView(ChallengeStageView):
    """Display an informational message and continue the flow."""

    response_class = MessageChallengeResponse

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()

    def get_challenge(self, *args: Any, **kwargs: Any) -> Challenge:
        current_stage = cast(MessageStage, self.executor.current_stage)
        return MessageChallenge(
            data={
                "name": current_stage.name,
                "title": current_stage.title,
                "message": current_stage.message,
                "button_text": current_stage.button_text,
            }
        )
