"""Authenticator Validation"""
from django.http import HttpRequest, HttpResponse
from django_otp import devices_for_user, user_has_device
from rest_framework.fields import CharField, DictField, IntegerField, JSONField, ListField
from structlog.stdlib import get_logger

from authentik.flows.challenge import (
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.models import NotConfiguredAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage

LOGGER = get_logger()


class AuthenticatorChallenge(WithUserInfoChallenge):
    """Authenticator challenge"""

    users_device_classes = ListField(child=CharField())
    class_challenges = DictField(JSONField())


class AuthenticatorChallengeResponse(ChallengeResponse):
    """Challenge used for Code-based authenticators"""

    device_challenges = DictField(JSONField())

    def validate_device_challenges(self, value: dict[str, dict]):
        return value


class AuthenticatorValidateStageView(ChallengeStageView):
    """Authenticator Validation"""

    response_class = AuthenticatorChallengeResponse

    allowed_device_classes: set[str]

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check if a user is set, and check if the user has any devices
        if not, we can skip this entire stage"""
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        has_devices = user_has_device(user)
        stage: AuthenticatorValidateStage = self.executor.current_stage

        user_devices = devices_for_user(self.get_pending_user())
        user_device_classes = set(
            [
                device.__class__.__name__.lower().replace("device", "")
                for device in user_devices
            ]
        )
        stage_device_classes = set(self.executor.current_stage.device_classes)
        self.allowed_device_classes = user_device_classes.intersection(stage_device_classes)

        # User has no devices, or the devices they have don't overlap with the allowed
        # classes
        if not has_devices or len(self.allowed_device_classes) < 1:
            if stage.not_configured_action == NotConfiguredAction.SKIP:
                LOGGER.debug("Authenticator not configured, skipping stage")
                return self.executor.stage_ok()
            if stage.not_configured_action == NotConfiguredAction.DENY:
                LOGGER.debug("Authenticator not configured, denying")
                return self.executor.stage_invalid()
        return super().get(request, *args, **kwargs)

    def get_challenge(self) -> AuthenticatorChallenge:
        return AuthenticatorChallenge(
            data={
                "type": ChallengeTypes.native,
                "component": "ak-stage-authenticator-validate",
                "users_device_classes": self.allowed_device_classes,
            }
        )

    def challenge_valid(
        self, challenge: AuthenticatorChallengeResponse
    ) -> HttpResponse:
        print(challenge)
        return HttpResponse()
