"""Login stage logic"""
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _

from authentik.core.models import User
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND

USER_LOGIN_AUTHENTICATED = "user_login_authenticated"


class UserLoginStageView(StageView):
    """Finalise Authentication flow by logging the user in"""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)

    def get(self, request: HttpRequest) -> HttpResponse:
        """Attach the currently pending user to the current session"""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            message = _("No Pending user to login.")
            messages.error(request, message)
            self.logger.debug(message)
            return self.executor.stage_invalid()
        backend = self.executor.plan.context.get(
            PLAN_CONTEXT_AUTHENTICATION_BACKEND, BACKEND_INBUILT
        )
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        if not user.is_active:
            self.logger.warning("User is not active, login will not work.")
        login(
            self.request,
            user,
            backend=backend,
        )
        delta = timedelta_from_string(self.executor.current_stage.session_duration)
        if delta.total_seconds() == 0:
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(delta)
        self.logger.debug(
            "Logged in",
            backend=backend,
            user=user,
            flow_slug=self.executor.flow.slug,
            session_duration=self.executor.current_stage.session_duration,
        )
        self.request.session[USER_LOGIN_AUTHENTICATED] = True
        messages.success(self.request, _("Successfully logged in!"))
        return self.executor.stage_ok()
