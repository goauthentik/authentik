"""Shared logout stages for SAML and OIDC providers"""

from django.http import HttpResponse
from rest_framework.fields import CharField, ListField

from authentik.core.api.utils import PassiveSerializer
from authentik.common.oauth.constants import PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.stage import ChallengeStageView
from authentik.providers.saml.views.flows import PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS


class LogoutURL(PassiveSerializer):
    """Data for a single logout URL"""

    url = CharField()
    saml_request = CharField(required=False, allow_null=True)
    saml_response = CharField(required=False, allow_null=True)
    relay_state = CharField(required=False, allow_null=True)
    provider_name = CharField(required=False, allow_null=True)
    binding = CharField(required=False, allow_null=True)


class IframeLogoutChallenge(Challenge):
    """Challenge for iframe logout"""

    component = CharField(default="ak-provider-iframe-logout")
    logout_urls = ListField(child=LogoutURL(), default=list)


class IframeLogoutChallengeResponse(ChallengeResponse):
    """Response for iframe logout"""

    component = CharField(default="ak-provider-iframe-logout")


class IframeLogoutStageView(ChallengeStageView):
    """SAML and OIDC Logout stage that handles parallel iframe logout"""

    response_class = IframeLogoutChallengeResponse

    def get_challenge(self) -> Challenge:
        """Generate iframe logout challenge for both SAML and OIDC"""
        logout_urls = []

        if self.executor.plan:
            saml_sessions = self.executor.plan.context.get(
                PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS, []
            )
            oidc_sessions = self.executor.plan.context.get(
                PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS, []
            )

            logout_urls.extend(saml_sessions)
            logout_urls.extend(oidc_sessions)

            self.executor.plan.context.pop(PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS, None)
            self.executor.plan.context.pop(PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS, None)
        else:
            saml_sessions = []
            oidc_sessions = []

        return IframeLogoutChallenge(
            data={
                "component": "ak-provider-iframe-logout",
                "logout_urls": logout_urls,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Iframe logout completed"""
        return self.executor.stage_ok()
