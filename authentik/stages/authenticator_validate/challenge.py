"""Validation stage challenge checking"""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField, ChoiceField, DateTimeField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.core.api.utils import JSONDictField, PassiveSerializer
from authentik.core.models import User
from authentik.core.signals import login_failed
from authentik.flows.stage import StageView
from authentik.stages.authenticator import devices_for_user
from authentik.stages.authenticator.models import Device, ThrottlingMixin
from authentik.stages.authenticator_validate.models import DeviceClasses
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD_ARGS

LOGGER = get_logger()


class DeviceChallenge(PassiveSerializer):
    """Single device challenge"""

    device_class = ChoiceField(choices=DeviceClasses.choices)
    device_uid = CharField()
    challenge = JSONDictField()
    last_used = DateTimeField(allow_null=True)


def validate_challenge_code(code: str, stage_view: StageView, user: User) -> Device:
    """Validate code-based challenges. We test against every device, on purpose, as
    the user mustn't choose between totp and static devices."""

    # audit_ignore decorator to prevent them being logged during authentication,
    # and to send them via SSF

    with transaction.atomic(), audit_ignore():
        for device in devices_for_user(user, for_verify=True):
            if isinstance(device, ThrottlingMixin):
                throttling_factor = stage_view.executor.current_stage.get_throttling_factor(
                    DeviceClasses.from_model_label(device.model_label())
                )
                if throttling_factor is not None:
                    device.set_throttle_factor(throttling_factor)
            if device.verify_token(code):
                break
        else:
            device = None

    if not device:
        login_failed.send(
            sender=__name__,
            credentials={"username": user.username},
            request=stage_view.request,
            stage=stage_view.executor.current_stage,
            context={
                PLAN_CONTEXT_METHOD_ARGS: {
                    "device_class": DeviceClasses.TOTP.value,
                }
            },
        )
        raise ValidationError(
            _("Invalid Token. Please ensure the time on your device is accurate and try again.")
        )
    return device
