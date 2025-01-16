"""authentik redirect stage"""

from urllib.parse import urlsplit

from django.http.response import HttpResponse
from rest_framework.fields import CharField

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    RedirectChallenge,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import (
    Flow,
)
from authentik.flows.planner import (
    PLAN_CONTEXT_IS_REDIRECTED,
    PLAN_CONTEXT_REDIRECT_STAGE_TARGET,
    FlowPlanner,
)
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_PLAN, InvalidStageError
from authentik.lib.utils.urls import reverse_with_qs
from authentik.stages.redirect.models import RedirectMode, RedirectStage

URL_SCHEME_FLOW = "ak-flow"


class RedirectChallengeResponse(ChallengeResponse):
    """Redirect challenge response"""

    component = CharField(default="xak-flow-redirect")
    to = CharField()


class RedirectStageView(ChallengeStageView):
    """Redirect stage to redirect to other Flows with context"""

    response_class = RedirectChallengeResponse

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()

    def parse_target(self, target: str) -> str | Flow:
        parsed_target = urlsplit(target)

        if parsed_target.scheme != URL_SCHEME_FLOW:
            return target

        flow = Flow.objects.filter(slug=parsed_target.netloc).first()
        if not flow:
            self.logger.warning(
                f"Flow set by {PLAN_CONTEXT_REDIRECT_STAGE_TARGET} does not exist",
                flow_slug=parsed_target.path,
            )
        return flow

    def switch_flow_with_context(self, flow: Flow, keep_context=True) -> str:
        """Switch to another flow, optionally keeping all context"""
        self.logger.info(
            "f(exec): Switching to new flow", new_flow=flow.slug, keep_context=keep_context
        )
        planner = FlowPlanner(flow)
        planner.use_cache = False
        default_context = self.executor.plan.context if keep_context else {}
        try:
            default_context[PLAN_CONTEXT_IS_REDIRECTED] = self.executor.flow
            plan = planner.plan(self.request, default_context)
        except FlowNonApplicableException as exc:
            raise InvalidStageError() from exc
        self.request.session[SESSION_KEY_PLAN] = plan
        kwargs = self.executor.kwargs
        kwargs.update({"flow_slug": flow.slug})
        return reverse_with_qs("authentik_core:if-flow", self.request.GET, kwargs=kwargs)

    def get_challenge(self, *args, **kwargs) -> Challenge:
        """Get the redirect target. Prioritize `redirect_stage_target` if present."""

        current_stage: RedirectStage = self.executor.current_stage
        target: str | Flow = ""

        target_url_override = self.executor.plan.context.get(PLAN_CONTEXT_REDIRECT_STAGE_TARGET, "")
        if target_url_override:
            target = self.parse_target(target_url_override)
        # `target` is false if the override was to a Flow but that Flow doesn't exist.
        if not target:
            if current_stage.mode == RedirectMode.STATIC:
                target = current_stage.target_static
            if current_stage.mode == RedirectMode.FLOW:
                target = current_stage.target_flow

        if isinstance(target, str):
            redirect_to = target
        else:
            redirect_to = self.switch_flow_with_context(
                target, keep_context=current_stage.keep_context
            )

        if not redirect_to:
            raise InvalidStageError(
                "No target found for Redirect stage. The stage's target_flow may have been deleted."
            )

        return RedirectChallenge(
            data={
                "component": "xak-flow-redirect",
                "to": redirect_to,
            }
        )
