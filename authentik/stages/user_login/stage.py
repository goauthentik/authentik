"""Login stage logic"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from rest_framework.fields import BooleanField, CharField

from authentik.core.models import Session, User
from authentik.events.middleware import audit_ignore
from authentik.flows.challenge import ChallengeResponse, WithUserInfoChallenge
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_SOURCE
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.user_login.middleware import (
    SESSION_KEY_BINDING_GEO,
    SESSION_KEY_BINDING_NET,
)
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
        return UserLoginChallenge(data={})

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Check for remember_me, and do login"""
        stage: UserLoginStage = self.executor.current_stage
        if timedelta_from_string(stage.remember_me_offset).total_seconds() > 0:
            return super().dispatch(request)
        return self.do_login(request)

    def challenge_valid(self, response: UserLoginChallengeResponse) -> HttpResponse:
        return self.do_login(self.request, response.validated_data["remember_me"])

    def set_session_duration(self, remember: bool) -> timedelta:
        """Update the sessions' expiry"""
        delta = timedelta_from_string(self.executor.current_stage.session_duration)
        if remember:
            offset = timedelta_from_string(self.executor.current_stage.remember_me_offset)
            delta = delta + offset
        if delta.total_seconds() == 0:
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(delta)
        return delta

    def set_session_ip(self):
        """Set the sessions' last IP and session bindings"""
        stage: UserLoginStage = self.executor.current_stage

        self.request.session[request.session.model.Keys.LAST_IP] = ClientIPMiddleware.get_client_ip(
            self.request
        )
        self.request.session[SESSION_KEY_BINDING_NET] = stage.network_binding
        self.request.session[SESSION_KEY_BINDING_GEO] = stage.geoip_binding

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
        delta = self.set_session_duration(remember)
        self.set_session_ip()
        # the `user_logged_in` signal will update the user to write the `last_login` field
        # which we don't want to log as we already have a dedicated login event
        with audit_ignore():
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
            Session.objects.filter(
                user=user,
            ).exclude(session_key=self.request.session.session_key).delete()
        return self.executor.stage_ok()
