"""Delete stage logic"""
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView

LOGGER = get_logger()


class UserDeleteStageView(StageView):
    """Finalise unenrollment flow by deleting the user object."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)

    def get(self, request: HttpRequest) -> HttpResponse:
        """Delete currently pending user"""
        user = self.get_pending_user()
        if not user.is_authenticated:
            message = _("No Pending User.")
            messages.error(request, message)
            LOGGER.debug(message)
            return self.executor.stage_invalid()
        logout(self.request)
        user.delete()
        LOGGER.debug("Deleted user", user=user)
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            del self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        return self.executor.stage_ok()
