from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.flows.challenge import Challenge
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_SOURCE, FlowPlan
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.sources.telegram.models import (
    GroupTelegramSourceConnection,
    TelegramSource,
    UserTelegramSourceConnection,
)
from authentik.sources.telegram.stage import TelegramChallengeResponse, TelegramLoginChallenge


class TelegramStartView(View):
    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        source = get_object_or_404(TelegramSource, slug=source_slug, enabled=True)
        plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]

        plan.insert_stage(in_memory_stage(TelegramLoginView), index=0)
        plan.context[PLAN_CONTEXT_SOURCE] = source
        flow = Flow.objects.get(pk=plan.flow_pk)

        return plan.to_redirect(self.request, flow)


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
