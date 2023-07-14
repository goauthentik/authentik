"""Deny stage logic"""
from django.http import HttpRequest, HttpResponse

from authentik.flows.stage import StageView


class DenyStageView(StageView):
    """Cancels the current flow"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Cancels the current flow"""
        return self.executor.stage_invalid()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
