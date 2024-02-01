"""Device validation base logic"""

from typing import TYPE_CHECKING

from django.http import QueryDict
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework.fields import CharField
from rest_framework.exceptions import ValidationError

from authentik.flows.challenge import ChallengeResponse, SubChallenge
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.lib.utils.reflection import all_subclasses

if TYPE_CHECKING:
    from authentik.stages.authenticator.models import Device


def challenge_types():
    """This function returns a mapping which contains all subclasses of challenges
    subclasses of Challenge, and Challenge itself."""
    mapping = {}
    for cls in all_subclasses(DeviceChallenge):
        mapping[cls().fields["component"].default] = cls
    return mapping


def challenge_response_types():
    """This function returns a mapping which contains all subclasses of challenges
    subclasses of Challenge, and Challenge itself."""
    mapping = {}
    for cls in all_subclasses(DeviceChallengeResponse):
        mapping[cls().fields["component"].default] = cls
    return mapping


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="DeviceChallengeTypes",
        serializers=challenge_types,
        resource_type_field_name="component",
    )
)
class DeviceChallenge(SubChallenge):
    """Challenge for an individual device, can contain data required
    to solve the devices' challenge"""

    device: "Device"

    component = CharField(default="ak-stage-authenticator-validate-device")
    uid = CharField()

    def __init__(self, *args, **kwargs):
        del self.fields["flow_info"]
        super().__init__(*args, **kwargs)


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="DeviceChallengeResponse",
        serializers=challenge_response_types,
        resource_type_field_name="component",
    )
)
class DeviceChallengeResponse[T: "Device"](SubChallenge, ChallengeResponse):
    """Response to a device's challenge. May continue additional fields depending
    of device type."""

    device: T

    component = CharField(default="ak-stage-authenticator-validate-device")
    uid = CharField()

    def __init__(self, instance=None, data=None, **kwargs):
        self.device = kwargs.pop("device", None)
        del self.fields["flow_info"]
        del self.fields["type"]
        super().__init__(instance=instance, data=data, **kwargs)


class DeviceValidator[T: "Device"](ChallengeStageView):
    """Device challenge validator, similar to a challenge stage view.
    Validation is intended to be done by the response class serializer,
    challenge_valid is not called on this class"""

    device: T

    response_class = DeviceChallengeResponse

    def __init__(self, executor: FlowExecutorView, device: T, **kwargs):
        super().__init__(executor, **kwargs)
        self.device = device
        self.request = executor.request

    def get_response_instance(self, data: QueryDict) -> ChallengeResponse:
        """Return the response class type"""
        return self.response_class(None, data=data, stage=self, device=self.device)

    def _get_challenge(self, *args, **kwargs) -> DeviceChallenge:
        challenge: DeviceChallenge = super()._get_challenge(*args, **kwargs)
        challenge.device = self.device
        challenge.initial_data["uid"] = generate_id()
        return challenge

    def device_allowed(self) -> bool:
        """Filter if a device is allowed to be used. By default only
        the confirmed flag is checked"""
        return self.device.confirmed

    def select_challenge(self, challenge: DeviceChallenge) -> DeviceChallenge:
        """Optional callback when a device challenge is selected"""
        return challenge

    def unselect_challenge(self, challenge: DeviceChallenge) -> DeviceChallenge:
        """Optional callback when a device challenge was selected and the user
        returns to the device picker"""
        return challenge
