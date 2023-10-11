"""Deny stage logic"""
from django.http import HttpRequest, HttpResponse

from authentik.flows.stage import StageView


class DenyStageView(StageView):
    """Cancels the current flow"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Cancels the current flow"""
        message = self.executor.plan.context.get(
            "deny_message", getattr(self.executor.current_stage, "deny_message")
        )
        return self.executor.stage_invalid(message)
