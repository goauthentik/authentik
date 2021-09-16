"""Deny stage logic"""
from django.http import HttpRequest, HttpResponse
from structlog.stdlib import get_logger

from authentik.flows.stage import StageView

LOGGER = get_logger()


class DenyStageView(StageView):
    """Cancells the current flow"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Cancells the current flow"""
        return self.executor.stage_invalid()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
