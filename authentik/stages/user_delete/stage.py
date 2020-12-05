"""Delete stage logic"""
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from structlog import get_logger

from authentik.core.models import User
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.stages.user_delete.forms import UserDeleteForm

LOGGER = get_logger()


class UserDeleteStageView(FormView, StageView):
    """Finalise unenrollment flow by deleting the user object."""

    form_class = UserDeleteForm

    def get(self, request: HttpRequest) -> HttpResponse:
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            message = _("No Pending User.")
            messages.error(request, message)
            LOGGER.debug(message)
            return self.executor.stage_invalid()
        return super().get(request)

    def form_valid(self, form: UserDeleteForm) -> HttpResponse:
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        user.delete()
        LOGGER.debug("Deleted user", user=user)
        del self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        return self.executor.stage_ok()
