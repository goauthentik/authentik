"""Source stage logic"""
from uuid import uuid4

from django.http import QueryDict
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now

from authentik.core.models import Source, User
from authentik.flows.challenge import Challenge, ChallengeTypes, RedirectChallenge
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_REDIRECT
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import QS_KEY_TOKEN, QS_QUERY
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.source.models import SourceStage

PLAN_CONTEXT_RESUME_TOKEN = "resume_token"


class SourceStageView(ChallengeStageView):
    """TODO."""

    def get_challenge(self, *args, **kwargs) -> Challenge:
        current_stage: SourceStage = self.executor.current_stage
        source: Source = current_stage.source
        resume_token = self.create_flow_token()
        login_button = source.ui_login_button(self.request)
        if not login_button:
            return self.executor.stage_invalid()
        # Old redirect is stored in the resume_token as that captures the flow in its current state
        self.executor.plan.context[PLAN_CONTEXT_REDIRECT] = self.get_full_url(
            **{QS_KEY_TOKEN: resume_token.key}
        )
        return login_button.challenge

    def create_flow_token(self) -> FlowToken:
        """Save the current flow state in a token that can be used to resume this flow"""
        pending_user: User = self.get_pending_user()
        current_stage: SourceStage = self.executor.current_stage
        identifier = slugify(f"ak-source-stage-{current_stage.name}-{str(uuid4())}")
        # Don't check for validity here, we only care if the token exists
        tokens = FlowToken.objects.filter(identifier=identifier)
        valid_delta = timedelta_from_string(current_stage.return_timeout)
        if not tokens.exists():
            return FlowToken.objects.create(
                expires=now() + valid_delta,
                user=pending_user,
                identifier=identifier,
                flow=self.executor.flow,
                _plan=FlowToken.pickle(self.executor.plan),
            )
        token = tokens.first()
        # Check if token is expired and rotate key if so
        if token.is_expired:
            token.expire_action()
        return token

    # TODO: Dedupe with email stage
    def get_full_url(self, **kwargs) -> str:
        """Get full URL to be used in template"""
        base_url = reverse(
            "authentik_core:if-flow",
            kwargs={"flow_slug": self.executor.flow.slug},
        )
        # Parse query string from current URL (full query string)
        # this view is only run within a flow executor, where we need to get the query string
        # from the query= parameter (double encoded); but for the redirect
        # we need to expand it since it'll go through the flow interface
        query_params = QueryDict(self.request.GET.get(QS_QUERY), mutable=True)
        query_params.pop(QS_KEY_TOKEN, None)
        query_params.update(kwargs)
        full_url = base_url
        if len(query_params) > 0:
            full_url = f"{full_url}?{query_params.urlencode()}"
        return self.request.build_absolute_uri(full_url)


class SourceStageResumeStage(ChallengeStageView):
    """Stage view used after the user returns from the source"""

    def get_challenge(self, *args, **kwargs) -> Challenge:
        token: FlowToken = self.executor.plan.context.get(PLAN_CONTEXT_RESUME_TOKEN)
        if not token:
            return self.executor.stage_invalid()
        url = self.get_full_url(**{QS_KEY_TOKEN: token.key})
        self.executor._flow_done()
        return RedirectChallenge(
            {
                "type": ChallengeTypes.REDIRECT,
                "to": str(url),
            }
        )
