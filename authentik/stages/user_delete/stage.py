"""Delete stage logic"""
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import User
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
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            message = _("No Pending User.")
            messages.error(request, message)
            LOGGER.debug(message)
            return self.executor.stage_invalid()
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        user.delete()
        LOGGER.debug("Deleted user", user=user)
        del self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        return self.executor.stage_ok()
