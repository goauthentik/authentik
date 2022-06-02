"""authentik password stage"""
from typing import Any, Optional

from django.contrib.auth import _clean_credentials
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.fields import CharField
from sentry_sdk.hub import Hub
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.reflection import path_to_class
from authentik.stages.password.models import PasswordStage

LOGGER = get_logger()
PLAN_CONTEXT_AUTHENTICATION_BACKEND = "user_backend"
PLAN_CONTEXT_METHOD = "auth_method"
PLAN_CONTEXT_METHOD_ARGS = "auth_method_args"
SESSION_KEY_INVALID_TRIES = "authentik/stages/password/user_invalid_tries"


def authenticate(request: HttpRequest, backends: list[str], **credentials: Any) -> Optional[User]:
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
        LOGGER.debug("Successful authentication", user=user, backend=backend_path)
        return user

    # The credentials supplied are invalid to all backends, fire signal
    user_login_failed.send(
        sender=__name__, credentials=_clean_credentials(credentials), request=request
    )


class PasswordChallenge(WithUserInfoChallenge):
    """Password challenge UI fields"""

    recovery_url = CharField(required=False)

    component = CharField(default="ak-stage-password")


class PasswordChallengeResponse(ChallengeResponse):
    """Password challenge response"""

    password = CharField(trim_whitespace=False)

    component = CharField(default="ak-stage-password")


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
            > current_stage.failed_attempts_before_cancel
        ):
            self.logger.debug("User has exceeded maximum tries")
            del self.request.session[SESSION_KEY_INVALID_TRIES]
            return self.executor.stage_invalid()
        return super().challenge_invalid(response)

    def challenge_valid(self, response: PasswordChallengeResponse) -> HttpResponse:
        """Authenticate against django's authentication backend"""
        if PLAN_CONTEXT_PENDING_USER not in self.executor.plan.context:
            return self.executor.stage_invalid()
        # Get the pending user's username, which is used as
        # an Identifier by most authentication backends
        pending_user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        auth_kwargs = {
            "password": response.validated_data.get("password", None),
            "username": pending_user.username,
        }
        try:
            with Hub.current.start_span(
                op="authentik.stages.password.authenticate",
                description="User authenticate call",
            ):
                user = authenticate(
                    self.request, self.executor.current_stage.backends, **auth_kwargs
                )
        except PermissionDenied:
            del auth_kwargs["password"]
            # User was found, but permission was denied (i.e. user is not active)
            self.logger.debug("Denied access", **auth_kwargs)
            return self.executor.stage_invalid()
        except ValidationError as exc:
            del auth_kwargs["password"]
            # User was found, authentication succeeded, but another signal raised an error
            # (most likely LDAP)
            self.logger.debug("Validation error from signal", exc=exc, **auth_kwargs)
            return self.executor.stage_invalid()
        else:
            if not user:
                # No user was found -> invalid credentials
                self.logger.debug("Invalid credentials")
                # Manually inject error into form
                response._errors.setdefault("password", [])
                response._errors["password"].append(ErrorDetail(_("Invalid password"), "invalid"))
                return self.challenge_invalid(response)
            # User instance returned from authenticate() has .backend property set
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
            self.executor.plan.context[PLAN_CONTEXT_AUTHENTICATION_BACKEND] = user.backend
            return self.executor.stage_ok()
