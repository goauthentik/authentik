"""Login stage logic"""
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from rest_framework.fields import BooleanField, CharField

from authentik.core.models import AuthenticatedSession, User
from authentik.flows.challenge import ChallengeResponse, ChallengeTypes, WithUserInfoChallenge
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_SOURCE
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.user_login.models import UserLoginStage


class UserLoginChallenge(WithUserInfoChallenge):
    """Empty challenge"""

    component = CharField(default="ak-stage-user-login")


class UserLoginChallengeResponse(ChallengeResponse):
    """User login challenge"""

    component = CharField(default="ak-stage-user-login")

    remember_me = BooleanField(required=True)


class UserLoginStageView(ChallengeStageView):
    """Finalise Authentication flow by logging the user in"""

    response_class = UserLoginChallengeResponse

    def get_challenge(self, *args, **kwargs) -> UserLoginChallenge:
        return UserLoginChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
            }
        )

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Check for remember_me, and do login"""
        stage: UserLoginStage = self.executor.current_stage
        if timedelta_from_string(stage.remember_me_offset).total_seconds() > 0:
            return super().dispatch(request)
        return self.do_login(request)

    def challenge_valid(self, response: UserLoginChallengeResponse) -> HttpResponse:
        return self.do_login(self.request, response.validated_data["remember_me"])

    def do_login(self, request: HttpRequest, remember: bool = False) -> HttpResponse:
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
        delta = timedelta_from_string(self.executor.current_stage.session_duration)
        if remember:
            offset = timedelta_from_string(self.executor.current_stage.remember_me_offset)
            delta = delta + offset
        if delta.total_seconds() == 0:
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(delta)
        login(
            self.request,
            user,
            backend=backend,
        )
        self.logger.debug(
            "Logged in",
            backend=backend,
            user=user.username,
            flow_slug=self.executor.flow.slug,
            session_duration=delta,
        )
        # Only show success message if we don't have a source in the flow
        # as sources show their own success messages
        if not self.executor.plan.context.get(PLAN_CONTEXT_SOURCE, None):
            messages.success(self.request, _("Successfully logged in!"))
        if self.executor.current_stage.terminate_other_sessions:
            AuthenticatedSession.objects.filter(
                user=user,
            ).exclude(session_key=self.request.session.session_key).delete()
        return self.executor.stage_ok()
