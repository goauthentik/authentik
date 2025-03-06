"""Delete stage logic"""

from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView


class UserDeleteStageView(StageView):
    """Finalise unenrollment flow by deleting the user object."""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Delete currently pending user"""
        user = self.get_pending_user()
        if not user.is_authenticated:
            self.logger.warning("No authenticated user")
            return self.executor.stage_invalid(_("No authenticated User."))
        logout(self.request)
        user.delete()
        self.logger.debug("Deleted user", user=user)
        if PLAN_CONTEXT_PENDING_USER in self.executor.plan.context:
            del self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        return self.executor.stage_ok()
