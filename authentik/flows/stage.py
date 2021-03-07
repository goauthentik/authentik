"""authentik stage Base view"""
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.http.request import QueryDict
from django.http.response import HttpResponse
from django.views.generic.base import View
from structlog.stdlib import get_logger
from rest_framework.request import Request

from authentik.core.models import DEFAULT_AVATAR, User
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    HttpChallengeResponse,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.views import FlowExecutorView

PLAN_CONTEXT_PENDING_USER_IDENTIFIER = "pending_user_identifier"
LOGGER = get_logger()


class StageView(View):
    """Abstract Stage, inherits TemplateView but can be combined with FormView"""

    executor: FlowExecutorView

    request: HttpRequest = None

    def __init__(self, executor: FlowExecutorView, **kwargs):
        self.executor = executor
        super().__init__(**kwargs)

    def get_pending_user(self) -> User:
        """Either show the matched User object or show what the user entered,
        based on what the earlier stage (mostly IdentificationStage) set.
        _USER_IDENTIFIER overrides the first User, as PENDING_USER is used for
        other things besides the form display.

        If no user is pending, returns request.user"""
        if PLAN_CONTEXT_PENDING_USER_IDENTIFIER in self.executor.plan.context:
            return User(
                username=self.executor.plan.context.get(
                    PLAN_CONTEXT_PENDING_USER_IDENTIFIER
                ),
                email="",
            )
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            return self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        return self.request.user


class ChallengeStageView(StageView):
    """Stage view which response with a challenge"""

    response_class = ChallengeResponse

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        """Return the response class type"""
        return self.response_class(None, data=data, stage=self)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Return a challenge for the frontend to solve"""
        challenge = self._get_challenge(*args, **kwargs)
        if not challenge.is_valid():
            LOGGER.warning(challenge.errors)
        return HttpChallengeResponse(challenge)

    # pylint: disable=unused-argument
    def post(self, request: Request, *args, **kwargs) -> HttpResponse:
        """Handle challenge response"""
        challenge: ChallengeResponse = self.get_response_instance(data=request.data)
        if not challenge.is_valid():
            return self.challenge_invalid(challenge)
        return self.challenge_valid(challenge)

    def _get_challenge(self, *args, **kwargs) -> Challenge:
        challenge = self.get_challenge(*args, **kwargs)
        if "title" not in challenge.initial_data:
            challenge.initial_data["title"] = self.executor.flow.title
        if isinstance(challenge, WithUserInfoChallenge):
            # If there's a pending user, update the `username` field
            # this field is only used by password managers.
            # If there's no user set, an error is raised later.
            if user := self.get_pending_user():
                challenge.initial_data["pending_user"] = user.username
            challenge.initial_data["pending_user_avatar"] = DEFAULT_AVATAR
            if not isinstance(user, AnonymousUser):
                challenge.initial_data["pending_user_avatar"] = user.avatar
        return challenge

    def get_challenge(self, *args, **kwargs) -> Challenge:
        """Return the challenge that the client should solve"""
        raise NotImplementedError

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Callback when the challenge has the correct format"""
        raise NotImplementedError

    def challenge_invalid(self, response: ChallengeResponse) -> HttpResponse:
        """Callback when the challenge has the incorrect format"""
        challenge_response = self._get_challenge()
        full_errors = {}
        for field, errors in response.errors.items():
            for error in errors:
                full_errors.setdefault(field, [])
                full_errors[field].append(
                    {
                        "string": str(error),
                        "code": error.code,
                    }
                )
        challenge_response.initial_data["response_errors"] = full_errors
        if not challenge_response.is_valid():
            LOGGER.warning(challenge_response.errors)
        return HttpChallengeResponse(challenge_response)
