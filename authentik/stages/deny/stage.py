"""Deny stage logic"""
from django.http import HttpRequest, HttpResponse

from authentik.flows.stage import StageView
from authentik.stages.deny.models import DenyStage


class DenyStageView(StageView):
    """Cancels the current flow"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Cancels the current flow"""
        stage: DenyStage = self.executor.current_stage
        message = self.executor.plan.context.get("deny_message", stage.deny_message)
        return self.executor.stage_invalid(message)
