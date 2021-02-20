"""authentik stage Base view"""
from collections import namedtuple
from typing import Any

from django.http import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    HttpChallengeResponse,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.views import FlowExecutorView

PLAN_CONTEXT_PENDING_USER_IDENTIFIER = "pending_user_identifier"

FakeUser = namedtuple("User", ["username", "email"])


class StageView(TemplateView):
    """Abstract Stage, inherits TemplateView but can be combined with FormView"""

    template_name = "login/form_with_user.html"

    executor: FlowExecutorView

    request: HttpRequest = None

    def __init__(self, executor: FlowExecutorView):
        self.executor = executor

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["title"] = self.executor.flow.title
        # Either show the matched User object or show what the user entered,
        # based on what the earlier stage (mostly IdentificationStage) set.
        # _USER_IDENTIFIER overrides the first User, as PENDING_USER is used for
        # other things besides the form display
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            kwargs["user"] = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        if PLAN_CONTEXT_PENDING_USER_IDENTIFIER in self.executor.plan.context:
            kwargs["user"] = FakeUser(
                username=self.executor.plan.context.get(
                    PLAN_CONTEXT_PENDING_USER_IDENTIFIER
                ),
                email="",
            )
        kwargs["primary_action"] = _("Continue")
        return super().get_context_data(**kwargs)


class ChallengeStageView(StageView):

    response_class = ChallengeResponse

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        challenge = self.get_challenge()
        challenge.is_valid()
        return HttpChallengeResponse(challenge)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        challenge: ChallengeResponse = self.response_class(data=request.POST)
        if not challenge.is_valid():
            return self.challenge_invalid(challenge)
        return self.challenge_valid(challenge)

    def get_challenge(self) -> Challenge:
        raise NotImplementedError

    def challenge_valid(self, challenge: ChallengeResponse) -> HttpResponse:
        raise NotImplementedError

    def challenge_invalid(self, challenge: ChallengeResponse) -> HttpResponse:
        return JsonResponse(challenge.errors)
