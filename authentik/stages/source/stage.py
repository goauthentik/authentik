"""Source stage logic"""
from typing import Any
from uuid import uuid4

from django.http import HttpRequest, QueryDict
from django.http.response import HttpResponse as HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Source, User
from authentik.core.types import UILoginButton
from authentik.flows.challenge import Challenge
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_REDIRECT
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import QS_KEY_TOKEN, QS_QUERY
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.source.models import SourceStage

PLAN_CONTEXT_RESUME_TOKEN = "resume_token"  # nosec


class SourceStageView(ChallengeStageView):
    """TODO."""

    login_button: UILoginButton

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        current_stage: SourceStage = self.executor.current_stage
        source: Source = (
            Source.objects.filter(pk=current_stage.source_id).select_subclasses().first()
        )
        if not source:
            self.logger.warning("Source does not exist")
            return self.executor.stage_invalid()
        self.login_button = source.ui_login_button(self.request)
        if not self.login_button:
            self.logger.warning("Source does not have a UI login button")
            return self.executor.stage_invalid()
        return super().dispatch(request, *args, **kwargs)

    def get_challenge(self, *args, **kwargs) -> Challenge:
        resume_token = self.create_flow_token()
        # Old redirect is stored in the resume_token as that captures the flow in its current state
        self.executor.plan.context[PLAN_CONTEXT_REDIRECT] = self.get_full_url(
            **{QS_KEY_TOKEN: resume_token.key}
        )
        return self.login_button.challenge

    def create_flow_token(self) -> FlowToken:
        """Save the current flow state in a token that can be used to resume this flow"""
        pending_user: User = self.get_pending_user()
        if pending_user.is_anonymous:
            pending_user = get_anonymous_user()
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
