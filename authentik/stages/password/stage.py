"""authentik password stage"""

from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField

from authentik.core.models import User
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallenge,
)
from authentik.flows.exceptions import StageInvalidException
from authentik.flows.models import Flow
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.policies.reputation.models import Reputation
from authentik.stages.password.auth import authenticate_password
from authentik.stages.password.lockout import PasswordAuthenticationStatus
from authentik.stages.password.models import PasswordStage

PLAN_CONTEXT_AUTHENTICATION_BACKEND = "user_backend"
PLAN_CONTEXT_METHOD = "auth_method"
PLAN_CONTEXT_METHOD_ARGS = "auth_method_args"
PLAN_CONTEXT_INITIAL_SCORE = "goauthentik.io/stages/password/initial_score"


class PasswordChallenge(WithUserInfoChallenge):
    """Password challenge UI fields"""

    recovery_url = CharField(required=False)

    component = CharField(default="ak-stage-password")

    allow_show_password = BooleanField(default=False)


class PasswordChallengeResponse(ChallengeResponse):
    """Password challenge response"""

    component = CharField(default="ak-stage-password")

    password = CharField(trim_whitespace=False)

    authentication_status = PasswordAuthenticationStatus.INVALID

    def validate_password(self, password: str) -> str | None:
        """Validate password and authenticate user"""
        executor = self.stage.executor
        if PLAN_CONTEXT_PENDING_USER not in executor.plan.context:
            raise StageInvalidException("No pending user")
        # Get the pending user's username, which is used as
        # an Identifier by most authentication backends
        pending_user: User = executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        try:
            result = authenticate_password(
                self.stage.request,
                executor.current_stage,
                pending_user,
                password,
                executor.current_stage,
            )
        except PermissionDenied as exc:
            # User was found, but permission was denied (i.e. user is not active)
            self.stage.logger.debug("Denied access", username=pending_user.username)
            raise StageInvalidException("Denied access") from exc
        except ValidationError as exc:
            # User was found, authentication succeeded, but another signal raised an error
            # (most likely LDAP)
            self.stage.logger.debug(
                "Validation error from signal",
                exc=exc,
                username=pending_user.username,
            )
            raise StageInvalidException("Validation error") from exc
        self.authentication_status = result.status
        if result.user is None:
            # No user was found -> invalid credentials
            self.stage.logger.info("Invalid credentials")
            error = _("Invalid password")
            if result.status is PasswordAuthenticationStatus.LAST_ATTEMPT:
                error = executor.current_stage.get_last_attempt_message(error)
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
        if response.authentication_status is PasswordAuthenticationStatus.LOCKED:
            return self.executor.stage_invalid(
                current_stage.get_lockout_message(_("Invalid password"))
            )
        initial_score = self.executor.plan.context.get(PLAN_CONTEXT_INITIAL_SCORE)
        if initial_score is None:
            initial_score = self.get_reputation_score()
            self.executor.plan.context[PLAN_CONTEXT_INITIAL_SCORE] = initial_score
        new_score = self.get_reputation_score()
        if (initial_score - new_score) >= current_stage.failed_attempts_before_cancel:
            self.logger.debug("User has exceeded maximum tries")
            return self.executor.stage_invalid(_("Invalid password"))
        return super().challenge_invalid(response)

    def challenge_valid(self, response: PasswordChallengeResponse) -> HttpResponse:
        """Authenticate against django's authentication backend"""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            return self.executor.stage_invalid()
        return self.executor.stage_ok()
