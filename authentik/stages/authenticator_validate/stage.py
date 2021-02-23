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
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage

LOGGER = get_logger()


class AuthenticatorChallenge(WithUserInfoChallenge):
    """Authenticator challenge"""

    device_challenges = ListField(child=DeviceChallenge())


class AuthenticatorChallengeResponse(ChallengeResponse):
    """Challenge used for Code-based authenticators"""

    response = DeviceChallenge()

    request: HttpRequest
    user: User

    def validate_response(self, value: DeviceChallenge):
        """Validate response"""
        return validate_challenge(value, self.request, self.user)


class AuthenticatorValidateStageView(ChallengeStageView):
    """Authenticator Validation"""

    response_class = AuthenticatorChallengeResponse

    challenges: list[DeviceChallenge]

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check if a user is set, and check if the user has any devices
        if not, we can skip this entire stage"""
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        stage: AuthenticatorValidateStage = self.executor.current_stage

        self.challenges = []
        user_devices = devices_for_user(self.get_pending_user())

        for device in user_devices:
            device_class = device.__class__.__name__.lower().replace("device", "")
            if device_class not in stage.device_classes:
                continue
            self.challenges.append(
                DeviceChallenge(
                    data={
                        "device_class": device_class,
                        "device_uid": device.pk,
                        "challenge": get_challenge_for_device(request, device),
                    }
                )
            )

        # No allowed devices
        if len(self.challenges) < 1:
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
                "device_challenges": self.challenges,
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
