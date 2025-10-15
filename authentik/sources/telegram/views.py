from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.flows.challenge import Challenge
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_REDIRECT,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET
from authentik.sources.telegram.models import (
    GroupTelegramSourceConnection,
    TelegramSource,
    UserTelegramSourceConnection,
)
from authentik.sources.telegram.stage import TelegramChallengeResponse, TelegramLoginChallenge


class TelegramStartView(View):
    def handle_login_flow(
        self, source: TelegramSource, *stages_to_append, **kwargs
    ) -> HttpResponse:
        """Prepare Authentication Plan, redirect user FlowExecutor"""
        # Ensure redirect is carried through when user was trying to
        # authorize application
        final_redirect = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, "authentik_core:if-user"
        )
        kwargs.update(
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_SOURCE: source,
                PLAN_CONTEXT_REDIRECT: final_redirect,
            }
        )
        # We run the Flow planner here so we can pass the Pending user in the context
        planner = FlowPlanner(source.pre_authentication_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(self.request, kwargs)
        except FlowNonApplicableException:
            raise Http404 from None
        for stage in stages_to_append:
            plan.append_stage(stage)
        return plan.to_redirect(self.request, source.pre_authentication_flow)

    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        source = get_object_or_404(TelegramSource, slug=source_slug, enabled=True)
        telegram_login_stage = in_memory_stage(TelegramLoginView)

        return self.handle_login_flow(source, telegram_login_stage)


class TelegramSourceFlowManager(SourceFlowManager):
    """Flow manager for Telegram source"""

    user_connection_type = UserTelegramSourceConnection
    group_connection_type = GroupTelegramSourceConnection


class TelegramLoginView(ChallengeStageView):

    response_class = TelegramChallengeResponse

    def dispatch(self, request, *args, **kwargs):
        self.source = self.executor.plan.context[PLAN_CONTEXT_SOURCE]
        return super().dispatch(request, *args, **kwargs)

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return TelegramLoginChallenge(
            data={
                "bot_username": self.source.bot_username,
                "request_message_access": self.source.request_message_access,
            },
        )

    def challenge_valid(self, response: TelegramChallengeResponse) -> HttpResponse:
        raw_info = response.validated_data.copy()
        raw_info.pop("component")
        raw_info.pop("hash")
        raw_info.pop("auth_date")
        source = self.source
        sfm = TelegramSourceFlowManager(
            source=source,
            request=self.request,
            identifier=raw_info["id"],
            user_info={"info": raw_info},
            policy_context={"telegram": raw_info},
        )
        return sfm.get_flow(
            raw_info=raw_info,
        )
