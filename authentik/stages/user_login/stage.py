"""Login stage logic"""

from datetime import datetime, timedelta
from hashlib import sha256

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from jwt import PyJWTError, decode, encode
from rest_framework.fields import BooleanField, CharField

from authentik.core import user_switching
from authentik.core.models import AuthenticatedSession, Session, User
from authentik.core.sessions import SessionStore
from authentik.events.middleware import audit_ignore
from authentik.flows.challenge import ChallengeResponse, WithUserInfoChallenge
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_USER_SWITCH_ADD_USER,
    PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION,
)
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.lib.utils.time import timedelta_from_string
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import (
    PLAN_CONTEXT_AUTHENTICATION_BACKEND,
    PLAN_CONTEXT_METHOD_ARGS,
)
from authentik.stages.user_login.middleware import (
    SESSION_KEY_BINDING_GEO,
    SESSION_KEY_BINDING_NET,
)
from authentik.stages.user_login.models import UserLoginStage
from authentik.tenants.utils import get_unique_identifier

COOKIE_NAME_KNOWN_DEVICE = "authentik_device"

PLAN_CONTEXT_METHOD_ARGS_KNOWN_DEVICE = "known_device"


class UserLoginChallenge(WithUserInfoChallenge):
    """Empty challenge"""

    component = CharField(default="ak-stage-user-login")


class UserLoginChallengeResponse(ChallengeResponse):
    """User login challenge"""

    component = CharField(default="ak-stage-user-login")

    remember_me = BooleanField(required=True)


class UserLoginStageView(ChallengeStageView):
    """Finalize Authentication flow by logging the user in"""

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

        self.request.session[self.request.session.model.Keys.LAST_IP] = (
            ClientIPMiddleware.get_client_ip(self.request)
        )
        self.request.session[SESSION_KEY_BINDING_NET] = stage.network_binding
        self.request.session[SESSION_KEY_BINDING_GEO] = stage.geoip_binding

    # FIXME: identical function in authenticator_validate
    @property
    def cookie_jwt_key(self) -> str:
        """Signing key for Known-device Cookie for this stage"""
        return sha256(
            f"{get_unique_identifier()}:{self.executor.current_stage.pk.hex}".encode("ascii")
        ).hexdigest()

    def set_known_device_cookie(self, user: User):
        """Set a cookie, valid longer than the session, which denotes that this user
        has logged in on this device before."""
        delta = timedelta_from_string(self.executor.current_stage.remember_device)
        response = self.executor.stage_ok()
        if delta.total_seconds() < 1:
            return response
        expiry = datetime.now() + delta
        cookie_payload = {
            "sub": user.uid,
            "exp": expiry.timestamp(),
        }
        cookie = encode(cookie_payload, self.cookie_jwt_key)
        response.set_cookie(
            COOKIE_NAME_KNOWN_DEVICE,
            cookie,
            expires=expiry,
            path=settings.SESSION_COOKIE_PATH,
            domain=settings.SESSION_COOKIE_DOMAIN,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        return response

    def is_known_device(self, user: User):
        """Returns `True` if the login happened on a "known" device, by the same user."""
        client_ip = ClientIPMiddleware.get_client_ip(self.request)
        if AuthenticatedSession.objects.filter(session__last_ip=client_ip, user=user).exists():
            return True
        if COOKIE_NAME_KNOWN_DEVICE not in self.request.COOKIES:
            return False
        try:
            payload = decode(
                self.request.COOKIES[COOKIE_NAME_KNOWN_DEVICE], self.cookie_jwt_key, ["HS256"]
            )
            if payload["sub"] == user.uid:
                return True
            return False
        except (PyJWTError, ValueError, TypeError) as exc:
            self.logger.info("eh", exc=exc)
            return False

    def _detach_session(self) -> None:
        """Continue on a new session so the current login stays usable as a switch target."""
        old_session = self.request.session
        flow_query_params = old_session.get(SESSION_KEY_GET)
        # Move the active plan so audit events keep context and old logins cannot resume it.
        old_session.pop(SESSION_KEY_PLAN, None)
        old_session.save()
        session_keys = old_session.model.Keys
        self.request.session = SessionStore(
            last_ip=old_session.get(session_keys.LAST_IP),
            last_user_agent=old_session.get(session_keys.LAST_USER_AGENT, ""),
        )
        self.request.session[SESSION_KEY_PLAN] = self.executor.plan
        if flow_query_params is not None:
            self.request.session[SESSION_KEY_GET] = flow_query_params

    def _get_valid_user_switch_target(self, user: User) -> AuthenticatedSession | None:
        """Return the live target session for an in-progress user switch."""
        target_session_id = self.executor.plan.context.get(PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION)
        if not target_session_id:
            return None
        return (
            user_switching.target_sessions(self.request, user.pk, target_session_id)
            .select_related("session", "user")
            .first()
        )

    def do_login(self, request: HttpRequest, remember: bool | None = None) -> HttpResponse:
        """Attach the currently pending user to the current session.
        `remember` Argument should be `None` if not configured, otherwise set to `True`/`False`
        representative of the user's choice."""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            message = _("No Pending user to login.")
            messages.error(request, message)
            self.logger.warning(message)
            return self.executor.stage_invalid()
        backend = self.executor.plan.context.get(
            PLAN_CONTEXT_AUTHENTICATION_BACKEND, BACKEND_INBUILT
        )
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        # This should realistically never happen: even though the
        # identification stage returns a fake user, any kind of authentication
        # would fail because the user doesn't exist. This is just a fallback
        # for a misconfiguration to prevent an exception.
        if user.pk is None:
            self.logger.debug("pending user is not saved, refusing to log in")
            return self.executor.stage_invalid()
        if PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION in self.executor.plan.context:
            target_session = self._get_valid_user_switch_target(user)
            if not target_session:
                message = _("The selected session is no longer available. Please try again.")
                self.logger.warning(message)
                return self.executor.stage_invalid(message)
            user = target_session.user
        if not user.is_active:
            self.logger.warning("User is not active, login will not work.")
            return self.executor.stage_invalid()
        is_user_switch_login = (
            PLAN_CONTEXT_USER_SWITCH_ADD_USER in self.executor.plan.context
            or PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION in self.executor.plan.context
        )
        user_switching_token = getattr(self.request, "user_switching_token", None)
        if (
            is_user_switch_login
            and self.request.user.is_authenticated
            and self.request.user.pk != user.pk
        ):
            self._detach_session()
            if user_switching_token:
                Session.objects.filter(
                    authenticatedsession__user=user,
                    authenticatedsession__user_switching_session_id=user_switching_token,
                ).delete()
        delta = self.set_session_duration(bool(remember))
        self.set_session_ip()
        # Check if the login request is coming from a known device
        self.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
        self.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS].setdefault(
            PLAN_CONTEXT_METHOD_ARGS_KNOWN_DEVICE, self.is_known_device(user)
        )
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
        if self.executor.current_stage.terminate_other_sessions:
            Session.objects.filter(
                authenticatedsession__user=user,
            ).exclude(session_key=self.request.session.session_key).delete()
        if remember is None:
            return self.set_known_device_cookie(user)
        return self.executor.stage_ok()
