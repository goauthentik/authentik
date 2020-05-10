"""Logout stage logic"""
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from structlog import get_logger

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import AuthenticationStage

LOGGER = get_logger()


class UserLogoutStageView(AuthenticationStage):
    """Finalise Authentication flow by logging the user in"""

    def get(self, request: HttpRequest) -> HttpResponse:
        logout(self.request)
        LOGGER.debug(
            "Logged out",
            user=self.executor.plan.context[PLAN_CONTEXT_PENDING_USER],
            flow_slug=self.executor.flow.slug,
        )
        return self.executor.stage_ok()
