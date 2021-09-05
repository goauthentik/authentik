"""Login stage logic"""
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND

LOGGER = get_logger()
USER_LOGIN_AUTHENTICATED = "user_login_authenticated"


class UserLoginStageView(StageView):
    """Finalise Authentication flow by logging the user in"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Attach the currently pending user to the current session"""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            message = _("No Pending user to login.")
            messages.error(request, message)
            LOGGER.debug(message)
            return self.executor.stage_invalid()
        backend = self.executor.plan.context.get(
            PLAN_CONTEXT_AUTHENTICATION_BACKEND, BACKEND_INBUILT
        )
        login(
            self.request,
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER],
            backend=backend,
        )
        delta = timedelta_from_string(self.executor.current_stage.session_duration)
        if delta.total_seconds() == 0:
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(delta)
        LOGGER.debug(
            "Logged in",
            backend=backend,
            user=self.executor.plan.context[PLAN_CONTEXT_PENDING_USER],
            flow_slug=self.executor.flow.slug,
            session_duration=self.executor.current_stage.session_duration,
        )
        self.request.session[USER_LOGIN_AUTHENTICATED] = True
        messages.success(self.request, _("Successfully logged in!"))
        return self.executor.stage_ok()
