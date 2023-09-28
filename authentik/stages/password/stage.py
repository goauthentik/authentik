"""authentik password stage"""
from typing import Any, Optional

from django.contrib.auth import _clean_credentials
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from sentry_sdk.hub import Hub
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.core.signals import login_failed
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.models import Flow, FlowDesignation, Stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.reflection import path_to_class
from authentik.stages.password.models import PasswordStage

LOGGER = get_logger()
PLAN_CONTEXT_AUTHENTICATION_BACKEND = "user_backend"
PLAN_CONTEXT_METHOD = "auth_method"
PLAN_CONTEXT_METHOD_ARGS = "auth_method_args"
SESSION_KEY_INVALID_TRIES = "authentik/stages/password/user_invalid_tries"


def authenticate(
    request: HttpRequest, backends: list[str], stage: Optional[Stage] = None, **credentials: Any
) -> Optional[User]:
    """If the given credentials are valid, return a User object.

    Customized version of django's authenticate, which accepts a list of backends"""
    for backend_path in backends:
        try:
            backend: BaseBackend = path_to_class(backend_path)()
        except ImportError:
            LOGGER.warning("Failed to import backend", path=backend_path)
            continue
        LOGGER.debug("Attempting authentication...", backend=backend_path)
        with Hub.current.start_span(
            op="authentik.stages.password.authenticate",
            description=backend_path,
        ):
            user = backend.authenticate(request, **credentials)
        if user is None:
            LOGGER.debug("Backend returned nothing, continuing", backend=backend_path)
            continue
        # Annotate the user object with the path of the backend.
        user.backend = backend_path
        LOGGER.info("Successful authentication", user=user.username, backend=backend_path)
        return user

    # The credentials supplied are invalid to all backends, fire signal
    login_failed.send(
        sender=__name__,
        credentials=_clean_credentials(credentials),
        request=request,
        stage=stage,
    )


class PasswordChallenge(WithUserInfoChallenge):
    """Password challenge UI fields"""

    recovery_url = CharField(required=False)

    component = CharField(default="ak-stage-password")


class PasswordChallengeResponse(ChallengeResponse):
    """Password challenge response"""

    component = CharField(default="ak-stage-password")

    password = CharField(trim_whitespace=False)

    def validate_password(self, password: str) -> str | None:
        """Validate password and authenticate user"""
        executor = self.stage.executor
        if PLAN_CONTEXT_PENDING_USER not in executor.plan.context:
            raise StageInvalidException("No pending user")
        # Get the pending user's username, which is used as
        # an Identifier by most authentication backends
        pending_user: User = executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        auth_kwargs = {
            "password": password,
            "username": pending_user.username,
        }
        try:
            with Hub.current.start_span(
                op="authentik.stages.password.authenticate",
                description="User authenticate call",
            ):
                user = authenticate(
                    self.stage.request,
                    executor.current_stage.backends,
                    executor.current_stage,
                    **auth_kwargs,
                )
        except PermissionDenied as exc:
            del auth_kwargs["password"]
            # User was found, but permission was denied (i.e. user is not active)
            self.stage.logger.debug("Denied access", **auth_kwargs)
            raise StageInvalidException("Denied access") from exc
        except ValidationError as exc:
            del auth_kwargs["password"]
            # User was found, authentication succeeded, but another signal raised an error
            # (most likely LDAP)
            self.stage.logger.debug("Validation error from signal", exc=exc, **auth_kwargs)
            raise StageInvalidException("Validation error") from exc
        if not user:
            # No user was found -> invalid credentials
            self.stage.logger.info("Invalid credentials")
            raise ValidationError(_("Invalid password"), "invalid")
        # User instance returned from authenticate() has .backend property set
        executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
        executor.plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = user.backend
        return password


class PasswordStageView(ChallengeStageView):
    """Authentication stage which authenticates against django's AuthBackend"""

    response_class = PasswordChallengeResponse

    def get_challenge(self) -> Challenge:
        challenge = PasswordChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
            }
        )
        recovery_flow = Flow.objects.filter(designation=FlowDesignation.RECOVERY)
        if recovery_flow.exists():
            recover_url = reverse(
                "authentik_core:if-flow",
                kwargs={"flow_slug": recovery_flow.first().slug},
            )
            challenge.initial_data["recovery_url"] = self.request.build_absolute_uri(recover_url)
        return challenge

    def challenge_invalid(self, response: PasswordChallengeResponse) -> HttpResponse:
        if SESSION_KEY_INVALID_TRIES not in self.request.session:
            self.request.session[SESSION_KEY_INVALID_TRIES] = 0
        self.request.session[SESSION_KEY_INVALID_TRIES] += 1
        current_stage: PasswordStage = self.executor.current_stage
        if (
            self.request.session[SESSION_KEY_INVALID_TRIES]
            >= current_stage.failed_attempts_before_cancel
        ):
            self.logger.debug("User has exceeded maximum tries")
            del self.request.session[SESSION_KEY_INVALID_TRIES]
            return self.executor.stage_invalid()
        return super().challenge_invalid(response)

    def challenge_valid(self, response: PasswordChallengeResponse) -> HttpResponse:
        """Authenticate against django's authentication backend"""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            return self.executor.stage_invalid()
        return self.executor.stage_ok()
