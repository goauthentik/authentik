"""Authenticator Validation"""
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django_otp import devices_for_user
from rest_framework.fields import ListField
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.challenge import (
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.models import NotConfiguredAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_validate.challenge import (
    DeviceChallenge,
    get_challenge_for_device,
    validate_challenge,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses

LOGGER = get_logger()

PER_DEVICE_CLASSES = [
    DeviceClasses.WEBAUTHN
]


class AuthenticatorChallenge(WithUserInfoChallenge):
    """Authenticator challenge"""

    device_challenges = ListField(child=DeviceChallenge())


class AuthenticatorChallengeResponse(ChallengeResponse, DeviceChallenge):
    """Challenge used for Code-based authenticators"""

    request: HttpRequest
    user: User

    def validate_challenge(self, value: dict):
        """Validate response"""
        return validate_challenge(value, self.request, self.user)


class AuthenticatorValidateStageView(ChallengeStageView):
    """Authenticator Validation"""

    response_class = AuthenticatorChallengeResponse

    def get_device_challenges(self) -> list[dict]:
        challenges = []
        user_devices = devices_for_user(self.get_pending_user())

        # static and totp are only shown once
        # since their challenges are device-independant
        seen_classes = []

        stage: AuthenticatorValidateStage = self.executor.current_stage

        for device in user_devices:
            device_class = device.__class__.__name__.lower().replace("device", "")
            if device_class not in stage.device_classes:
                continue
            # Ensure only classes in PER_DEVICE_CLASSES are returned per device
            # otherwise only return a single challenge
            if device_class in seen_classes and device_class not in PER_DEVICE_CLASSES:
                continue
            if device_class not in seen_classes:
                seen_classes.append(device_class)
            challenges.append(
                DeviceChallenge(
                    data={
                        "device_class": device_class,
                        "device_uid": device.pk,
                        "challenge": get_challenge_for_device(self.request, device),
                    }
                ).initial_data
            )
        return challenges

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check if a user is set, and check if the user has any devices
        if not, we can skip this entire stage"""
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        stage: AuthenticatorValidateStage = self.executor.current_stage
        challenges = self.get_device_challenges()
        self.request.session["device_challenges"] = challenges

        # No allowed devices
        if len(challenges) < 1:
            if stage.not_configured_action == NotConfiguredAction.SKIP:
                LOGGER.debug("Authenticator not configured, skipping stage")
                return self.executor.stage_ok()
            if stage.not_configured_action == NotConfiguredAction.DENY:
                LOGGER.debug("Authenticator not configured, denying")
                return self.executor.stage_invalid()
        return super().get(request, *args, **kwargs)

    def get_challenge(self) -> AuthenticatorChallenge:
        challenges = self.request.session["device_challenges"]
        return AuthenticatorChallenge(
            data={
                "type": ChallengeTypes.native,
                "component": "ak-stage-authenticator-validate",
                "device_challenges": challenges,
            }
        )

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        response: AuthenticatorChallengeResponse = super().get_response_instance(data)
        response.request = self.request
        response.user = self.get_pending_user()
        return response

    def challenge_valid(
        self, challenge: AuthenticatorChallengeResponse
    ) -> HttpResponse:
        print(challenge)
        return HttpResponse()
