"""Source stage logic"""

from typing import Any
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.utils.text import slugify
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Source, User
from authentik.core.sources.flow_manager import SESSION_KEY_OVERRIDE_FLOW_TOKEN
from authentik.core.types import UILoginButton
from authentik.enterprise.stages.source.models import SourceStage
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_IS_RESTORED
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.time import timedelta_from_string

PLAN_CONTEXT_RESUME_TOKEN = "resume_token"  # nosec


class SourceStageView(ChallengeStageView):
    """Suspend the current flow execution and send the user to a source,
    after which this flow execution is resumed."""

    login_button: UILoginButton

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        current_stage: SourceStage = self.executor.current_stage
        source: Source = (
            Source.objects.filter(pk=current_stage.source_id).select_subclasses().first()
        )
        if not source:
            self.logger.warning("Source does not exist")
            return self.executor.stage_invalid("Source does not exist")
        self.login_button = source.ui_login_button(self.request)
        if not self.login_button:
            self.logger.warning("Source does not have a UI login button")
            return self.executor.stage_invalid("Invalid source")
        restore_token = self.executor.plan.context.get(PLAN_CONTEXT_IS_RESTORED)
        override_token = self.request.session.get(SESSION_KEY_OVERRIDE_FLOW_TOKEN)
        if restore_token and override_token and restore_token.pk == override_token.pk:
            del self.request.session[SESSION_KEY_OVERRIDE_FLOW_TOKEN]
            return self.executor.stage_ok()
        return super().dispatch(request, *args, **kwargs)

    def get_challenge(self, *args, **kwargs) -> Challenge:
        resume_token = self.create_flow_token()
        self.request.session[SESSION_KEY_OVERRIDE_FLOW_TOKEN] = resume_token
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
        valid_delta = timedelta_from_string(current_stage.resume_timeout)
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

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()
