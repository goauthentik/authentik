"""Authenticator Validation"""

from datetime import datetime
from hashlib import sha256
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from jwt import PyJWTError, decode, encode
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ListField, SerializerMethodField, UUIDField

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.flows.challenge import ChallengeResponse, ChallengeTypes, WithUserInfoChallenge
from authentik.flows.exceptions import FlowSkipStageException
from authentik.flows.models import FlowDesignation, NotConfiguredAction, Stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.time import timedelta_from_string
from authentik.root.install_id import get_install_id
from authentik.stages.authenticator import devices_for_user
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator.validate import (
    DeviceChallenge,
    DeviceChallengeResponse,
    DeviceValidator,
    challenge_types,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
from authentik.stages.authenticator_webauthn.validate import WebAuthnDeviceValidator
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

COOKIE_NAME_MFA = "authentik_mfa"

PLAN_CONTEXT_STAGES = "goauthentik.io/stages/authenticator_validate/stages"
PLAN_CONTEXT_SELECTED_STAGE = "goauthentik.io/stages/authenticator_validate/selected_stage"
PLAN_CONTEXT_DEVICE_CHALLENGES = "goauthentik.io/stages/authenticator_validate/device_challenges"
PLAN_CONTEXT_SELECTED_CHALLENGE = "goauthentik.io/stages/authenticator_validate/selected_challenge"


class SelectableStageSerializer(PassiveSerializer):
    """Serializer for stages which can be selected by users"""

    pk = UUIDField()
    name = CharField()
    verbose_name = CharField()
    meta_model_name = CharField()


class AuthenticatorValidationChallenge(WithUserInfoChallenge):
    """Authenticator challenge"""

    component = CharField(default="ak-stage-authenticator-validate")

    device_challenges = SerializerMethodField()
    configuration_stages = ListField(child=SelectableStageSerializer())

    @extend_schema_field(
        ListField(
            child=PolymorphicProxySerializer(
                component_name="DeviceChallengeTypes",
                serializers=challenge_types,
                resource_type_field_name="component",
            )
        )
    )
    def get_device_challenges(self, _) -> list[DeviceChallenge]:
        """Device challenges"""
        # We don't want to just have the serializer set as ListField(DeviceChallenge)
        # as that will only return the fields common to DeviceChallenge
        # so since we do the serializer validation earlier and just return the data
        return self.initial_data["device_challenges"]


class AuthenticatorValidationChallengeResponse(ChallengeResponse):
    """Challenge wrapper for authenticator devices"""

    component = CharField(default="ak-stage-authenticator-validate")

    device: Optional[Device]

    selected_challenge_uid = CharField(required=False, allow_null=True)
    selected_challenge_response = DeviceChallengeResponse(required=False)
    selected_stage = CharField(required=False)

    def replace_device_challenge(self, challenge: DeviceChallenge):
        """Replace a device challenge in the flow plan"""
        challenges = self.stage.executor.plan.context.get(PLAN_CONTEXT_DEVICE_CHALLENGES, [])
        self.stage.executor.plan.context[PLAN_CONTEXT_DEVICE_CHALLENGES] = [
            challenge if x.data["uid"] == challenge.data["uid"] else x for x in challenges
        ]

    def get_device_validator(self, challenge: DeviceChallenge) -> DeviceValidator:
        """Get the device validator used for this challenge's device"""
        device = challenge.device
        device_validator_type: type[DeviceValidator] = device.validator
        device_validator = device_validator_type(self.stage.executor, device)
        if not device_validator.device_allowed():
            self.stage.logger.debug("Device not allowed, skipping", device=device)
            raise ValidationError("Invalid device")
        return device_validator

    def _select_challenge(self, challenge: Optional[DeviceChallenge]):
        """Helper to select a challenge, which also notifies the device validator
        to unselect the previous challenge"""
        previous_challenge: Optional[DeviceChallenge] = self.stage.executor.plan.context.get(
            PLAN_CONTEXT_SELECTED_CHALLENGE, None
        )
        # if the challenge uids haven't changed, no callbacks are triggered
        if (
            previous_challenge
            and challenge
            and previous_challenge.data["uid"] == challenge.data["uid"]
        ):
            return
        if previous_challenge:
            # Notify device validator that its challenge is unselected
            self.stage.logger.debug("Unselecting device challenge", challenge=previous_challenge)
            new_unselect = self.get_device_validator(previous_challenge).unselect_challenge(
                previous_challenge
            )
            # Replace old unselected challenge with a potentially modified one
            self.replace_device_challenge(new_unselect)
            self.stage.executor.plan.context.pop(PLAN_CONTEXT_SELECTED_CHALLENGE, None)
        if challenge:
            # Notify the device validator that it has been selected
            self.stage.logger.debug("Selecting device challenge", challenge=challenge)
            new_selected = self.get_device_validator(challenge).select_challenge(challenge)
            # Replace old unselected challenge with a potentially modified one
            self.replace_device_challenge(new_selected)
            self.stage.executor.plan.context[PLAN_CONTEXT_SELECTED_CHALLENGE] = new_selected

    def validate_selected_challenge_uid(self, uid: Optional[str]) -> DeviceChallenge:
        if not uid:
            # Unselect previous challenge if set
            self._select_challenge(None)
        device_challenges: list[DeviceChallenge] = self.stage.executor.plan.context.get(
            PLAN_CONTEXT_DEVICE_CHALLENGES, []
        )
        for allowed_challenge in device_challenges:
            if allowed_challenge.data["uid"] != uid:
                continue
            self._select_challenge(allowed_challenge)
            return allowed_challenge
        raise ValidationError("No compatible device class allowed")

    def validate_selected_stage(self, stage_pk: str) -> str:
        """Check that the selected stage is valid"""
        stages = self.stage.executor.plan.context.get(PLAN_CONTEXT_STAGES, [])
        if not any(str(stage.pk) == stage_pk for stage in stages):
            raise ValidationError("Selected stage is invalid")
        self.stage.logger.debug("Setting selected stage to ", stage=stage_pk)
        # Setting this directly in the flow plan circumvents the validation
        # as we're guaranteed to be redirected
        self.stage.executor.plan.context[PLAN_CONTEXT_SELECTED_STAGE] = stage_pk
        return stage_pk

    def validate(self, data: dict):
        if PLAN_CONTEXT_SELECTED_STAGE in self.stage.executor.plan.context:
            return data
        device_challenge: DeviceChallenge = data.get("selected_challenge_uid")
        # We have to get the response data from `initial_data` so
        # it's not pre-validated. As the class only has the field defined
        # as the base serializer, this will loose all custom attributes
        # from subclasses
        device_challenge_response: dict = self.initial_data.get("selected_challenge_response")
        if not device_challenge or not device_challenge_response:
            raise ValidationError("Missing device response")
        device = device_challenge.device
        # Notify the device validator that it has been selected
        device_validator_type: type[DeviceValidator] = device.validator
        device_validator = device_validator_type(self.stage.executor, device)
        if not device_validator.device_allowed():
            self.stage.logger.debug("Device not allowed, skipping", device=device)
            raise ValidationError("Invalid device")
        self.stage.logger.debug(
            "Validating device challenge response", challenge=device_challenge_response
        )
        response = device_validator.get_response_instance(device_challenge_response)
        response.is_valid(raise_exception=True)
        self.stage.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD, "auth_mfa")
        self.stage.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
        self.stage.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS].setdefault("mfa_devices", [])
        self.stage.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS]["mfa_devices"].append(device)
        self.device = device
        return data


class AuthenticatorValidateStageView(ChallengeStageView):
    """Authenticator Validation"""

    response_class = AuthenticatorValidationChallengeResponse

    def get_device_challenges(self) -> list[DeviceChallenge]:
        """Get a list of all device challenges applicable for the current stage"""
        challenges = []
        # Convert to a list to have usable log output instead of just <generator ...>
        user_devices = list(devices_for_user(self.get_pending_user()))
        self.logger.debug("Got devices for user", devices=user_devices)

        stage: AuthenticatorValidateStage = self.executor.current_stage

        threshold = timedelta_from_string(stage.last_auth_threshold)
        allowed_devices = []

        for device in user_devices:
            device_class = device.__class__.__name__.lower().replace("device", "")
            if device_class not in stage.device_classes:
                self.logger.debug("device class not allowed", device_class=device_class)
                continue
            device_validator_type: type[DeviceValidator] = device.validator
            device_validator = device_validator_type(self.executor, device)
            if not device_validator.device_allowed():
                self.logger.debug("Device not allowed, skipping", device=device)
                continue
            challenge = device_validator._get_challenge()
            challenge.is_valid()
            challenges.append(challenge)
            allowed_devices.append(device)
            self.logger.debug("adding challenge for device", challenge=challenge)
        # check if we have an MFA cookie and if it's valid
        if threshold.total_seconds() > 0:
            self.check_mfa_cookie(allowed_devices)
        return challenges

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
                webauthn_challenge = WebAuthnDeviceValidator.get_webauthn_challenge_without_user(
                    self.request, stage.webauthn_user_verification
                )
                challenges = [webauthn_challenge]
            else:
                self.logger.debug("No pending user, continuing")
                return self.executor.stage_ok()
        if PLAN_CONTEXT_DEVICE_CHALLENGES in self.executor.plan.context:
            challenges = self.executor.plan.context[PLAN_CONTEXT_DEVICE_CHALLENGES]
        else:
            self.executor.plan.context[PLAN_CONTEXT_DEVICE_CHALLENGES] = challenges

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
            self.executor.plan.context[PLAN_CONTEXT_SELECTED_STAGE] = next_stage
            # Because that normal execution only happens on post, we directly inject it here and
            # return it
            self.executor.plan.insert_stage(next_stage)
            return self.executor.stage_ok()
        stages = Stage.objects.filter(pk__in=stage.configuration_stages.all()).select_subclasses()
        self.executor.plan.context[PLAN_CONTEXT_STAGES] = stages
        return super().get(self.request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        res = super().post(request, *args, **kwargs)
        if (
            PLAN_CONTEXT_SELECTED_STAGE in self.executor.plan.context
            and self.executor.current_stage.not_configured_action == NotConfiguredAction.CONFIGURE
        ):
            self.logger.debug("Got selected stage in context, running that")
            stage_pk = self.executor.plan.context.get(PLAN_CONTEXT_SELECTED_STAGE)
            # Because the foreign key to stage.configuration_stage points to
            # a base stage class, we need to do another lookup
            stage = Stage.objects.get_subclass(pk=stage_pk)
            # plan.insert inserts at 1 index, so when stage_ok pops 0,
            # the configuration stage is next
            self.executor.plan.insert_stage(stage)
            return self.executor.stage_ok()
        return res

    def get_challenge(self) -> AuthenticatorValidationChallenge:
        challenges = self.executor.plan.context.get(PLAN_CONTEXT_DEVICE_CHALLENGES, [])
        stages = self.executor.plan.context.get(PLAN_CONTEXT_STAGES, [])
        stage_challenges = []
        for stage in stages:
            serializer = SelectableStageSerializer(
                data={
                    "pk": stage.pk,
                    "name": stage.friendly_name or stage.name,
                    "verbose_name": str(stage._meta.verbose_name)
                    .replace("Setup Stage", "")
                    .strip(),
                    "meta_model_name": f"{stage._meta.app_label}.{stage._meta.model_name}",
                }
            )
            serializer.is_valid()
            stage_challenges.append(serializer.data)
        return AuthenticatorValidationChallenge(
            data={
                "component": "ak-stage-authenticator-validate",
                "type": ChallengeTypes.NATIVE.value,
                "device_challenges": [x.data for x in challenges],
                "configuration_stages": stage_challenges,
            }
        )

    @property
    def cookie_jwt_key(self) -> str:
        """Signing key for MFA Cookie for this stage"""
        return sha256(
            f"{get_install_id()}:{self.executor.current_stage.pk.hex}".encode("ascii")
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
        # FIXME: this probably should also be part of the validator
        if not user and isinstance(response.device, WebAuthnDevice):
            self.logger.debug("Set user from user-less flow", user=response.device.user)
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = response.device.user
            self.executor.plan.context[PLAN_CONTEXT_METHOD] = "auth_webauthn_pwl"
            self.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS] = {
                "device": response.device,
            }
        return self.set_valid_mfa_cookie(response.device)
