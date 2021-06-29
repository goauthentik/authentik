"""Authenticator Validation"""
from django.http import HttpRequest, HttpResponse
from django_otp import devices_for_user
from rest_framework.fields import CharField, IntegerField, JSONField, ListField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.flows.challenge import (
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.models import NotConfiguredAction, Stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_validate.challenge import (
    DeviceChallenge,
    get_challenge_for_device,
    validate_challenge_code,
    validate_challenge_duo,
    validate_challenge_webauthn,
)
from authentik.stages.authenticator_validate.models import (
    AuthenticatorValidateStage,
    DeviceClasses,
)

LOGGER = get_logger()

PER_DEVICE_CLASSES = [DeviceClasses.WEBAUTHN]


class AuthenticatorValidationChallenge(WithUserInfoChallenge):
    """Authenticator challenge"""

    device_challenges = ListField(child=DeviceChallenge())
    component = CharField(default="ak-stage-authenticator-validate")


class AuthenticatorValidationChallengeResponse(ChallengeResponse):
    """Challenge used for Code-based and WebAuthn authenticators"""

    code = CharField(required=False)
    webauthn = JSONField(required=False)
    duo = IntegerField(required=False)
    component = CharField(default="ak-stage-authenticator-validate")

    def _challenge_allowed(self, classes: list):
        device_challenges: list[dict] = self.stage.request.session.get(
            "device_challenges"
        )
        if not any(x["device_class"] in classes for x in device_challenges):
            raise ValidationError("No compatible device class allowed")

    def validate_code(self, code: str) -> str:
        """Validate code-based response, raise error if code isn't allowed"""
        self._challenge_allowed([DeviceClasses.TOTP, DeviceClasses.STATIC])
        return validate_challenge_code(
            code, self.stage.request, self.stage.get_pending_user()
        )

    def validate_webauthn(self, webauthn: dict) -> dict:
        """Validate webauthn response, raise error if webauthn wasn't allowed
        or response is invalid"""
        self._challenge_allowed([DeviceClasses.WEBAUTHN])
        return validate_challenge_webauthn(
            webauthn, self.stage.request, self.stage.get_pending_user()
        )

    def validate_duo(self, duo: int) -> int:
        """Initiate Duo authentication"""
        self._challenge_allowed([DeviceClasses.DUO])
        return validate_challenge_duo(
            duo, self.stage.request, self.stage.get_pending_user()
        )

    def validate(self, data: dict):
        # Checking if the given data is from a valid device class is done above
        # Here we only check if the any data was sent at all
        if "code" not in data and "webauthn" not in data and "duo" not in data:
            raise ValidationError("Empty response")
        return data


class AuthenticatorValidateStageView(ChallengeStageView):
    """Authenticator Validation"""

    response_class = AuthenticatorValidationChallengeResponse

    def get_device_challenges(self) -> list[dict]:
        """Get a list of all device challenges applicable for the current stage"""
        challenges = []
        user_devices = devices_for_user(self.get_pending_user())
        LOGGER.debug("Got devices for user", devices=user_devices)

        # static and totp are only shown once
        # since their challenges are device-independant
        seen_classes = []

        stage: AuthenticatorValidateStage = self.executor.current_stage

        for device in user_devices:
            device_class = device.__class__.__name__.lower().replace("device", "")
            if device_class not in stage.device_classes:
                LOGGER.debug("device class not allowed", device_class=device_class)
                continue
            # Ensure only classes in PER_DEVICE_CLASSES are returned per device
            # otherwise only return a single challenge
            if device_class in seen_classes and device_class not in PER_DEVICE_CLASSES:
                continue
            if device_class not in seen_classes:
                seen_classes.append(device_class)
            challenge = DeviceChallenge(
                data={
                    "device_class": device_class,
                    "device_uid": device.pk,
                    "challenge": get_challenge_for_device(self.request, device),
                }
            )
            challenge.is_valid()
            challenges.append(challenge.data)
            LOGGER.debug("adding challenge for device", challenge=challenge)
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
            if stage.not_configured_action == NotConfiguredAction.CONFIGURE:
                LOGGER.debug("Authenticator not configured, sending user to configure")
                # Because the foreign key to stage.configuration_stage points to
                # a base stage class, we need to do another lookup
                stage = Stage.objects.get_subclass(pk=stage.configuration_stage.pk)
                # plan.insert inserts at 1 index, so when stage_ok pops 0,
                # the configuration stage is next
                self.executor.plan.insert_stage(stage)
                return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def get_challenge(self) -> AuthenticatorValidationChallenge:
        challenges = self.request.session["device_challenges"]
        return AuthenticatorValidationChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "device_challenges": challenges,
            }
        )

    # pylint: disable=unused-argument
    def challenge_valid(
        self, challenge: AuthenticatorValidationChallengeResponse
    ) -> HttpResponse:
        # All validation is done by the serializer
        return self.executor.stage_ok()
