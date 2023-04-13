"""Authenticator Validation"""
from datetime import datetime
from hashlib import sha256
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django_otp import devices_for_user
from django_otp.models import Device
from jwt import PyJWTError, decode, encode
from rest_framework.fields import CharField, IntegerField, JSONField, ListField, UUIDField
from rest_framework.serializers import ValidationError

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.flows.challenge import ChallengeResponse, ChallengeTypes, WithUserInfoChallenge
from authentik.flows.exceptions import FlowSkipStageException
from authentik.flows.models import FlowDesignation, NotConfiguredAction, Stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.stages.authenticator_sms.models import SMSDevice
from authentik.stages.authenticator_validate.challenge import (
    DeviceChallenge,
    get_challenge_for_device,
    get_webauthn_challenge_without_user,
    select_challenge,
    validate_challenge_code,
    validate_challenge_duo,
    validate_challenge_webauthn,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

COOKIE_NAME_MFA = "authentik_mfa"

SESSION_KEY_STAGES = "authentik/stages/authenticator_validate/stages"
SESSION_KEY_SELECTED_STAGE = "authentik/stages/authenticator_validate/selected_stage"
SESSION_KEY_DEVICE_CHALLENGES = "authentik/stages/authenticator_validate/device_challenges"


class SelectableStageSerializer(PassiveSerializer):
    """Serializer for stages which can be selected by users"""

    pk = UUIDField()
    name = CharField()
    verbose_name = CharField()
    meta_model_name = CharField()


class AuthenticatorValidationChallenge(WithUserInfoChallenge):
    """Authenticator challenge"""

    device_challenges = ListField(child=DeviceChallenge())
    component = CharField(default="ak-stage-authenticator-validate")
    configuration_stages = ListField(child=SelectableStageSerializer())


class AuthenticatorValidationChallengeResponse(ChallengeResponse):
    """Challenge used for Code-based and WebAuthn authenticators"""

    device: Optional[Device]

    selected_challenge = DeviceChallenge(required=False)
    selected_stage = CharField(required=False)

    code = CharField(required=False)
    webauthn = JSONField(required=False)
    duo = IntegerField(required=False)
    component = CharField(default="ak-stage-authenticator-validate")

    def _challenge_allowed(self, classes: list):
        device_challenges: list[dict] = self.stage.request.session.get(
            SESSION_KEY_DEVICE_CHALLENGES, []
        )
        if not any(x["device_class"] in classes for x in device_challenges):
            raise ValidationError("No compatible device class allowed")

    def validate_code(self, code: str) -> str:
        """Validate code-based response, raise error if code isn't allowed"""
        self._challenge_allowed([DeviceClasses.TOTP, DeviceClasses.STATIC, DeviceClasses.SMS])
        self.device = validate_challenge_code(code, self.stage, self.stage.get_pending_user())
        return code

    def validate_webauthn(self, webauthn: dict) -> dict:
        """Validate webauthn response, raise error if webauthn wasn't allowed
        or response is invalid"""
        self._challenge_allowed([DeviceClasses.WEBAUTHN])
        self.device = validate_challenge_webauthn(
            webauthn, self.stage, self.stage.get_pending_user()
        )
        return webauthn

    def validate_duo(self, duo: int) -> int:
        """Initiate Duo authentication"""
        self._challenge_allowed([DeviceClasses.DUO])
        self.device = validate_challenge_duo(duo, self.stage, self.stage.get_pending_user())
        return duo

    def validate_selected_challenge(self, challenge: dict) -> dict:
        """Check which challenge the user has selected. Actual logic only used for SMS stage."""
        # First check if the challenge is valid
        allowed = False
        for device_challenge in self.stage.request.session.get(SESSION_KEY_DEVICE_CHALLENGES, []):
            if device_challenge.get("device_class", "") == challenge.get(
                "device_class", ""
            ) and device_challenge.get("device_uid", "") == challenge.get("device_uid", ""):
                allowed = True
        if not allowed:
            raise ValidationError("invalid challenge selected")

        if challenge.get("device_class", "") != "sms":
            return challenge
        devices = SMSDevice.objects.filter(pk=int(challenge.get("device_uid", "0")))
        if not devices.exists():
            raise ValidationError("invalid challenge selected")
        select_challenge(self.stage.request, devices.first())
        return challenge

    def validate_selected_stage(self, stage_pk: str) -> str:
        """Check that the selected stage is valid"""
        stages = self.stage.request.session.get(SESSION_KEY_STAGES, [])
        if not any(str(stage.pk) == stage_pk for stage in stages):
            raise ValidationError("Selected stage is invalid")
        self.stage.logger.debug("Setting selected stage to ", stage=stage_pk)
        self.stage.request.session[SESSION_KEY_SELECTED_STAGE] = stage_pk
        return stage_pk

    def validate(self, attrs: dict):
        # Checking if the given data is from a valid device class is done above
        # Here we only check if the any data was sent at all
        if "code" not in attrs and "webauthn" not in attrs and "duo" not in attrs:
            raise ValidationError("Empty response")
        self.stage.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD, "auth_mfa")
        self.stage.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
        self.stage.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS].setdefault("mfa_devices", [])
        self.stage.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS]["mfa_devices"].append(
            self.device
        )
        return attrs


class AuthenticatorValidateStageView(ChallengeStageView):
    """Authenticator Validation"""

    response_class = AuthenticatorValidationChallengeResponse

    def get_device_challenges(self) -> list[dict]:
        """Get a list of all device challenges applicable for the current stage"""
        challenges = []
        # Convert to a list to have usable log output instead of just <generator ...>
        user_devices = list(devices_for_user(self.get_pending_user()))
        self.logger.debug("Got devices for user", devices=user_devices)

        # static and totp are only shown once
        # since their challenges are device-independent
        seen_classes = []

        stage: AuthenticatorValidateStage = self.executor.current_stage

        threshold = timedelta_from_string(stage.last_auth_threshold)
        allowed_devices = []

        for device in user_devices:
            device_class = device.__class__.__name__.lower().replace("device", "")
            if device_class not in stage.device_classes:
                self.logger.debug("device class not allowed", device_class=device_class)
                continue
            if isinstance(device, SMSDevice) and device.is_hashed:
                self.logger.debug("Hashed SMS device, skipping")
                continue
            allowed_devices.append(device)
            # Ensure only one challenge per device class
            # WebAuthn does another device loop to find all WebAuthn devices
            if device_class in seen_classes:
                continue
            if device_class not in seen_classes:
                seen_classes.append(device_class)
            challenge = DeviceChallenge(
                data={
                    "device_class": device_class,
                    "device_uid": device.pk,
                    "challenge": get_challenge_for_device(self.request, stage, device),
                }
            )
            challenge.is_valid()
            challenges.append(challenge.data)
            self.logger.debug("adding challenge for device", challenge=challenge)
        # check if we have an MFA cookie and if it's valid
        if threshold.total_seconds() > 0:
            self.check_mfa_cookie(allowed_devices)
        return challenges

    def get_webauthn_challenge_without_user(self) -> list[dict]:
        """Get a WebAuthn challenge when no pending user is set."""
        challenge = DeviceChallenge(
            data={
                "device_class": DeviceClasses.WEBAUTHN,
                "device_uid": -1,
                "challenge": get_webauthn_challenge_without_user(
                    self.request,
                    self.executor.current_stage,
                ),
            }
        )
        challenge.is_valid()
        return [challenge.data]

    # pylint: disable=too-many-return-statements
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check if a user is set, and check if the user has any devices
        if not, we can skip this entire stage"""
        user = self.get_pending_user()
        stage: AuthenticatorValidateStage = self.executor.current_stage
        if user and not user.is_anonymous:
            try:
                challenges = self.get_device_challenges()
            except FlowSkipStageException:
                return self.executor.stage_ok()
        else:
            if self.executor.flow.designation != FlowDesignation.AUTHENTICATION:
                self.logger.debug("Refusing passwordless flow in non-authentication flow")
                return self.executor.stage_ok()
            # Passwordless auth, with just webauthn
            if DeviceClasses.WEBAUTHN in stage.device_classes:
                self.logger.debug("Flow without user, getting generic webauthn challenge")
                challenges = self.get_webauthn_challenge_without_user()
            else:
                self.logger.debug("No pending user, continuing")
                return self.executor.stage_ok()
        self.request.session[SESSION_KEY_DEVICE_CHALLENGES] = challenges

        # No allowed devices
        if len(challenges) < 1:
            if stage.not_configured_action == NotConfiguredAction.SKIP:
                self.logger.debug("Authenticator not configured, skipping stage")
                return self.executor.stage_ok()
            if stage.not_configured_action == NotConfiguredAction.DENY:
                self.logger.debug("Authenticator not configured, denying")
                return self.executor.stage_invalid()
            if stage.not_configured_action == NotConfiguredAction.CONFIGURE:
                self.logger.debug("Authenticator not configured, forcing configure")
                return self.prepare_stages(user)
        return super().get(request, *args, **kwargs)

    def prepare_stages(self, user: User, *args, **kwargs) -> HttpResponse:
        """Check how the user can configure themselves. If no stages are set, return an error.
        If a single stage is set, insert that stage directly. If multiple are selected, include
        them in the challenge."""
        stage: AuthenticatorValidateStage = self.executor.current_stage
        if not stage.configuration_stages.exists():
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=(
                    "Authenticator validation stage is set to configure user "
                    "but no configuration flow is set."
                ),
                stage=self,
            ).from_http(self.request).set_user(user).save()
            return self.executor.stage_invalid()
        if stage.configuration_stages.count() == 1:
            next_stage = Stage.objects.get_subclass(pk=stage.configuration_stages.first().pk)
            self.logger.debug("Single stage configured, auto-selecting", stage=next_stage)
            self.request.session[SESSION_KEY_SELECTED_STAGE] = next_stage
            # Because that normal execution only happens on post, we directly inject it here and
            # return it
            self.executor.plan.insert_stage(next_stage)
            return self.executor.stage_ok()
        stages = Stage.objects.filter(pk__in=stage.configuration_stages.all()).select_subclasses()
        self.request.session[SESSION_KEY_STAGES] = stages
        return super().get(self.request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        res = super().post(request, *args, **kwargs)
        if (
            SESSION_KEY_SELECTED_STAGE in self.request.session
            and self.executor.current_stage.not_configured_action == NotConfiguredAction.CONFIGURE
        ):
            self.logger.debug("Got selected stage in session, running that")
            stage_pk = self.request.session.get(SESSION_KEY_SELECTED_STAGE)
            # Because the foreign key to stage.configuration_stage points to
            # a base stage class, we need to do another lookup
            stage = Stage.objects.get_subclass(pk=stage_pk)
            # plan.insert inserts at 1 index, so when stage_ok pops 0,
            # the configuration stage is next
            self.executor.plan.insert_stage(stage)
            return self.executor.stage_ok()
        return res

    def get_challenge(self) -> AuthenticatorValidationChallenge:
        challenges = self.request.session.get(SESSION_KEY_DEVICE_CHALLENGES, [])
        stages = self.request.session.get(SESSION_KEY_STAGES, [])
        stage_challenges = []
        for stage in stages:
            serializer = SelectableStageSerializer(
                data={
                    "pk": stage.pk,
                    "name": stage.name,
                    "verbose_name": str(stage._meta.verbose_name),
                    "meta_model_name": f"{stage._meta.app_label}.{stage._meta.model_name}",
                }
            )
            serializer.is_valid()
            stage_challenges.append(serializer.data)
        return AuthenticatorValidationChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "device_challenges": challenges,
                "configuration_stages": stage_challenges,
            }
        )

    @property
    def cookie_jwt_key(self) -> str:
        """Signing key for MFA Cookie for this stage"""
        return sha256(
            f"{settings.SECRET_KEY}:{self.executor.current_stage.pk.hex}".encode("ascii")
        ).hexdigest()

    def check_mfa_cookie(self, allowed_devices: list[Device]):
        """Check if an MFA cookie has been set, whether it's valid and applies
        to the current stage and device.

        The list of devices passed to this function must only contain devices for the
        correct user and with an allowed class"""
        if COOKIE_NAME_MFA not in self.request.COOKIES:
            return
        stage: AuthenticatorValidateStage = self.executor.current_stage
        threshold = timedelta_from_string(stage.last_auth_threshold)
        latest_allowed = datetime.now() + threshold
        try:
            payload = decode(self.request.COOKIES[COOKIE_NAME_MFA], self.cookie_jwt_key, ["HS256"])
            if payload["stage"] != stage.pk.hex:
                self.logger.warning("Invalid stage PK")
                return
            if datetime.fromtimestamp(payload["exp"]) > latest_allowed:
                self.logger.warning("Expired MFA cookie")
                return
            if not any(device.pk == payload["device"] for device in allowed_devices):
                self.logger.warning("Invalid device PK")
                return
            self.logger.info("MFA has been used within threshold")
            raise FlowSkipStageException()
        except (PyJWTError, ValueError, TypeError) as exc:
            self.logger.info("Invalid mfa cookie for device", exc=exc)

    def set_valid_mfa_cookie(self, device: Device) -> HttpResponse:
        """Set an MFA cookie to allow users to skip MFA validation in this context (browser)

        The cookie is JWT which is signed with a hash of the secret key and the UID of the stage"""
        stage: AuthenticatorValidateStage = self.executor.current_stage
        delta = timedelta_from_string(stage.last_auth_threshold)
        if delta.total_seconds() < 1:
            self.logger.info("Not setting MFA cookie since threshold is not set.")
            return self.executor.stage_ok()
        expiry = datetime.now() + delta
        cookie_payload = {
            "device": device.pk,
            "stage": stage.pk.hex,
            "exp": expiry.timestamp(),
        }
        response = self.executor.stage_ok()
        cookie = encode(cookie_payload, self.cookie_jwt_key)
        response.set_cookie(
            COOKIE_NAME_MFA,
            cookie,
            expires=expiry,
            path=settings.SESSION_COOKIE_PATH,
            domain=settings.SESSION_COOKIE_DOMAIN,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        return response

    def challenge_valid(self, response: AuthenticatorValidationChallengeResponse) -> HttpResponse:
        # All validation is done by the serializer
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user and "webauthn" in response.data:
            webauthn_device: WebAuthnDevice = response.device
            self.logger.debug("Set user from user-less flow", user=webauthn_device.user)
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = webauthn_device.user
            self.executor.plan.context[PLAN_CONTEXT_METHOD] = "auth_webauthn_pwl"
            self.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS] = {
                "device": webauthn_device,
            }
        return self.set_valid_mfa_cookie(response.device)

    def cleanup(self):
        self.request.session.pop(SESSION_KEY_STAGES, None)
        self.request.session.pop(SESSION_KEY_SELECTED_STAGE, None)
        self.request.session.pop(SESSION_KEY_DEVICE_CHALLENGES, None)
