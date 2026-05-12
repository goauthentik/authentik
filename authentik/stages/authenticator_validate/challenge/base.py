import uuid
from dataclasses import dataclass

from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField, ChoiceField, DateTimeField

from authentik.core.api.utils import JSONDictField, PassiveSerializer
from authentik.core.models import Application, User
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses


class DeviceChallenge(PassiveSerializer):
    """Single device challenge"""

    device_class = ChoiceField(choices=DeviceClasses.choices)
    device_uid = CharField(allow_null=True)
    challenge = JSONDictField()
    last_used = DateTimeField(allow_null=True)
    uid = CharField()


class ChallengeValidationError(Exception):
    def __init__(
        self,
        detail: str,
        code: str | None = None,
        device: Device | None = None,
        failure_context: dict = None,
    ):
        if failure_context is None:
            failure_context = {}
        self.detail = detail
        self.device = device
        self.code = code
        self.failure_context = failure_context


@dataclass
class FlowContext:
    application: Application | None = None


class DeviceChallenger:
    """
    A DeviceChallenger codifies the challenge generation and validation logic for a specific
    authenticator device type.
    A subclass must implement the following methods:
    - `make_device_challenge`: Generate a challenge for a device
    - `initiate`: Initiate a challenge (e.g. send a code to the device)
    - `validate`: Validate a challenge response
    A subclass must also define the `device_class` class attribute as the type of
    device it works with.
    """

    device_class: type[Device]

    __subclasses: dict[type[Device], type[DeviceChallenger]] = {}

    def __init__(
        self,
        request: HttpRequest,
        validate_stage: AuthenticatorValidateStage,
        flow_context: FlowContext,
    ):
        self.request = request
        self.validate_stage = validate_stage
        self.flow_context = flow_context

    def get_allowed_devices(self, user: User) -> list[Device]:
        """Override this to restrict the devices a user can use for MFA"""
        return list(self.device_class.objects.filter(user=user))

    def _make_device_challenge(
        self, device: Device | None, user: User | None, challenge: dict
    ) -> DeviceChallenge:
        """Helper to wrap a device-specific challenge in a DeviceChallenge object"""
        last_used = None
        if device:
            last_used = device.last_used
        elif user is not None:
            last_used_device = (
                self.device_class.objects.filter(user=user, last_used__isnull=False)
                .order_by("-last_used")
                .first()
            )
            if last_used_device:
                last_used = last_used_device.last_used
        return DeviceChallenge(
            data=dict(
                uid=uuid.uuid4().hex,
                device_class=DeviceClasses.from_model(self.device_class),
                device_uid=device.pk if device else None,
                challenge=challenge,
                last_used=last_used,
            )
        )

    def make_device_challenges(self, user: User) -> list[DeviceChallenge]:
        """
        Generate a set of challenges for the user. Usually, this will be one challenge per device,
        but for some device types a single aggregate challenge can be issued for all user's devices.
        """
        raise NotImplementedError()

    def make_identification_challenge(self) -> DeviceChallenge | None:
        """
        Make a challenge that can be used to identify the user.
        Used for passwordless authentication.
        :return: A challenge, or None if the device type does not support user identification
        """
        return None

    def initiate(self, device_challenge: dict):
        """
        Initiate the challenge after the user has selected it. Usually that would mean
        either sending a code to the user or doing nothing.
        """
        raise NotImplementedError()

    def validate(
        self, devices: QuerySet[Device], challenge: dict, challenge_response: str | dict
    ) -> Device:
        """
        Validate a challenge response. The device must be selected from the `devices` queryset.
        The caller is responsible for pre-selecting the devices depending on validation context
        (user's devices for the second factor, all devices if the user is being identified).
        :return: Upon successful validation, the device that matched the challenge.
        :raises ChallengeValidationError: If the challenge is invalid
        """
        raise NotImplementedError()

    @staticmethod
    def get_subclass_for_device_type(device_type: type[Device]) -> type[DeviceChallenger]:
        try:
            return DeviceChallenger.__subclasses[device_type]
        except KeyError:
            raise NotImplementedError(f"No DeviceChallenger for {device_type}") from None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "device_class"):
            raise TypeError(f"DeviceChallenger subclass {cls.__name__} must define 'device_class'")
        cls.__subclasses[cls.device_class] = cls


class DeviceDependentValidationMixin:
    """
    Validate the challenge response against a specific single device.
    `.validate` will expect a QuerySet with a single device.
    """

    def validate(
        self, devices: QuerySet[Device], challenge: dict, challenge_response: str
    ) -> Device:
        with transaction.atomic():
            try:
                device = devices.select_for_update().get()
            except Device.DoesNotExist as exc:
                raise ChallengeValidationError(_("Unknown device.")) from exc
            device.set_throttle_factor(
                self.validate_stage.get_throttling_factor(
                    DeviceClasses.from_model(self.device_class)
                )
            )
            success = device.verify_token(challenge_response)
        if success:
            return device
        else:
            raise ChallengeValidationError(_("Invalid Token."), device=device)


class DeviceIndependentValidationMixin:
    """
    Validate the challenge response against all devices of a given type.
    Normally, a caller of `.validate` will need to ensure that the devices belong to the same user.
    """

    validation_error_message = _("Invalid Token.")

    def validate(
        self, devices: QuerySet[Device], challenge: dict, challenge_response: str | dict
    ) -> Device:
        successful_device = None
        with transaction.atomic():
            for device in devices.select_for_update():
                device.set_throttle_factor(
                    self.validate_stage.get_throttling_factor(
                        DeviceClasses.from_model(self.device_class)
                    )
                )
                if device.verify_token(challenge_response):
                    successful_device = device
                    break
        if successful_device:
            return successful_device
        else:
            raise ChallengeValidationError(
                self.validation_error_message,
            )
