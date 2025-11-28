"""SAML Logout stages for automatic injection"""

from django.http import HttpResponse
from rest_framework.fields import BooleanField, CharField
from structlog.stdlib import get_logger

from authentik.flows.challenge import Challenge, ChallengeResponse, HttpChallengeResponse
from authentik.flows.stage import ChallengeStageView
from authentik.providers.saml.views.flows import PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS

LOGGER = get_logger()


class NativeLogoutStageViewBase(ChallengeStageView):
    """Base class for native browser logout stages with shared functionality"""


class NativeLogoutChallenge(Challenge):
    """Challenge for native browser logout"""

    component = CharField(default="ak-provider-saml-native-logout")
    post_url = CharField(required=False)
    saml_request = CharField(required=False)
    relay_state = CharField(required=False)
    provider_name = CharField(required=False)
    binding = CharField(required=False)
    redirect_url = CharField(required=False)
    is_complete = BooleanField(required=False, default=False)


class NativeLogoutChallengeResponse(ChallengeResponse):
    """Response for native browser logout"""

    component = CharField(default="ak-provider-saml-native-logout")


class NativeLogoutStageView(NativeLogoutStageViewBase):
    """Native browser logout stage that handles redirect chain and post logouts."""

    response_class = NativeLogoutChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        """Generate challenge for next provider"""
        pending = self.executor.plan.context.get(PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS, [])
        if not pending:
            self.executor.plan.context.pop(PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS, None)
            return NativeLogoutChallenge(
                data={
                    "component": "ak-provider-saml-native-logout",
                    "is_complete": True,
                }
            )

        logout_data = pending.pop(0)
        self.executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS] = pending

        return NativeLogoutChallenge(
            data={
                "component": "ak-provider-saml-native-logout",
                **logout_data,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Challenge completed"""
        challenge = self.get_challenge()

        if not challenge.is_valid():
            return self.executor.stage_invalid()

        if challenge.initial_data.get("is_complete"):
            return self.executor.stage_ok()

        return HttpChallengeResponse(challenge)
