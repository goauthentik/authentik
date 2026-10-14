"""Authenticator devices helpers"""

from typing import TYPE_CHECKING

from django.db import transaction

if TYPE_CHECKING:
    from authentik.core.models import User


def verify_token(user, device_id, token):
    """Verify a token against a specific device, identified by its persistent_id.
    Runs in a transaction so throttling is enforced."""
    from authentik.stages.authenticator.models import Device

    verified = None
    with transaction.atomic():
        device = Device.from_persistent_id(device_id, for_verify=True)
        if (device is not None) and (device.user_id == user.pk) and device.verify_token(token):
            verified = device

    return verified


def match_token(user, token):
    """Verify a token against all of a user's devices, returning the first match"""
    with transaction.atomic():
        for device in devices_for_user(user, for_verify=True):
            if device.verify_token(token):
                break
        else:
            device = None

    return device


def devices_for_user(user: User, confirmed: bool | None = True, for_verify: bool = False):
    """Iterate all devices of a user, optionally filtered by `confirmed`.
    With `for_verify`, devices are locked with select_for_update, so this must
    be called inside a transaction."""
    if user.is_anonymous:
        return

    for model in device_classes():
        device_set = model.objects.devices_for_user(user, confirmed=confirmed)
        if for_verify:
            device_set = device_set.select_for_update()

        yield from device_set


def user_has_device(user, confirmed=True):
    """Check if a user has at least one device"""
    try:
        next(devices_for_user(user, confirmed=confirmed))
    except StopIteration:
        has_device = False
    else:
        has_device = True

    return has_device


def device_classes():
    """Iterate all loaded device models"""
    from django.apps import apps

    from authentik.stages.authenticator.models import Device

    for config in apps.get_app_configs():
        for model in config.get_models():
            if issubclass(model, Device):
                yield model
