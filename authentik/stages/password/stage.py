"""authentik password stage"""

from typing import TYPE_CHECKING, Any

from django.contrib.auth import _clean_credentials
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField
from sentry_sdk import start_span
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.core.signals import login_failed
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallenge,
)
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.models import Flow, Stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.reflection import path_to_class
from authentik.policies.reputation.models import Reputation
from authentik.stages.password.models import PasswordStage

if TYPE_CHECKING:
    from authentik.enterprise.stages.password.lockout import PasswordLockoutResult

LOGGER = get_logger()
PLAN_CONTEXT_AUTHENTICATION_BACKEND = "user_backend"
PLAN_CONTEXT_METHOD = "auth_method"
PLAN_CONTEXT_METHOD_ARGS = "auth_method_args"
PLAN_CONTEXT_INITIAL_SCORE = "goauthentik.io/stages/password/initial_score"


def authenticate(
    request: HttpRequest, backends: list[str], stage: Stage | None = None, **credentials: Any
) -> User | None:
    """If the given credentials are valid, return a User object.

    Customized version of django's authenticate, which accepts a list of backends"""
    for backend_path in backends:
        try:
            backend: BaseBackend = path_to_class(backend_path)()
        except ImportError:
            LOGGER.warning("Failed to import backend", path=backend_path)
            continue
        LOGGER.debug("Attempting authentication...", backend=backend_path)
        with start_span(
            op="authentik.stages.password.authenticate",
            name=backend_path,
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

    allow_show_password = BooleanField(default=False)


class PasswordChallengeResponse(ChallengeResponse):
    """Password challenge response"""

    component = CharField(default="ak-stage-password")

    password = CharField(trim_whitespace=False)

    lockout: PasswordLockoutResult | None = None

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
            with start_span(
                op="authentik.stages.password.authenticate",
                name="User authenticate call",
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
        from authentik.enterprise.stages.password.lockout import PasswordLockout

        result = PasswordLockout(executor.current_stage, self.stage.request).apply(
            pending_user, user, executor.plan.context
        )
        self.lockout = result
        if not result.user:
            # No user was found -> invalid credentials
            self.stage.logger.info("Invalid credentials")
            error = _("Invalid password")
            if result.last_attempt:
                error = executor.current_stage.last_attempt_warning_message or error
            raise ValidationError(error, "invalid")
        # User instance returned from authenticate() has .backend property set
        executor.plan.context[PLAN_CONTEXT_PENDING_USER] = result.user
        executor.plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = result.user.backend
        return password


class PasswordStageView(ChallengeStageView):
    """Authentication stage which authenticates against django's AuthBackend"""

    response_class = PasswordChallengeResponse

    def get_challenge(self) -> Challenge:
        challenge = PasswordChallenge(
            data={
                "allow_show_password": self.executor.current_stage.allow_show_password,
            }
        )
        recovery_flow: Flow | None = self.request.brand.flow_recovery
        if recovery_flow:
            recover_url = reverse(
                "authentik_core:if-flow",
                kwargs={"flow_slug": recovery_flow.slug},
            )
            challenge.initial_data["recovery_url"] = self.request.build_absolute_uri(recover_url)
        if PLAN_CONTEXT_INITIAL_SCORE not in self.executor.plan.context:
            self.executor.plan.context[PLAN_CONTEXT_INITIAL_SCORE] = self.get_reputation_score()
        return challenge

    def get_reputation_score(self) -> int:
        return (
            Reputation.objects.filter(identifier=self.get_pending_user().username).aggregate(
                total_score=Sum("score")
            )["total_score"]
            or 0
        )

    def challenge_invalid(self, response: PasswordChallengeResponse) -> HttpResponse:
        current_stage: PasswordStage = self.executor.current_stage
        error = _("Invalid password")
        if response.lockout:
            if response.lockout.lockout_reached:
                return self.executor.stage_invalid(current_stage.lockout_message or error)
            if response.lockout.last_attempt:
                error = current_stage.last_attempt_warning_message or error
        initial_score = self.executor.plan.context.get(PLAN_CONTEXT_INITIAL_SCORE)
        if initial_score is None:
            initial_score = self.get_reputation_score()
            self.executor.plan.context[PLAN_CONTEXT_INITIAL_SCORE] = initial_score
        new_score = self.get_reputation_score()
        if (initial_score - new_score) >= current_stage.failed_attempts_before_cancel:
            self.logger.debug("User has exceeded maximum tries")
            return self.executor.stage_invalid(error)
        return super().challenge_invalid(response)

    def challenge_valid(self, response: PasswordChallengeResponse) -> HttpResponse:
        """Authenticate against django's authentication backend"""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            return self.executor.stage_invalid()
        return self.executor.stage_ok()
