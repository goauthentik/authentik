"""Authenticator devices helpers"""
from django.db import transaction


def verify_token(user, device_id, token):
    """
    Attempts to verify a :term:`token` against a specific device, identified by
    :attr:`~authentik.stages.authenticator.models.Device.persistent_id`.

    This wraps the verification process in a transaction to ensure that things
    like throttling polices are properly enforced.

    :param user: The user supplying the token.
    :type user: :class:`~django.contrib.auth.models.User`

    :param str device_id: A device's persistent_id value.

    :param str token: An OTP token to verify.

    :returns: The device that accepted ``token``, if any.
    :rtype: :class:`~authentik.stages.authenticator.models.Device` or ``None``

    """
    from authentik.stages.authenticator.models import Device

    verified = None
    with transaction.atomic():
        device = Device.from_persistent_id(device_id, for_verify=True)
        if (device is not None) and (device.user_id == user.pk) and device.verify_token(token):
            verified = device

    return verified


def match_token(user, token):
    """
    Attempts to verify a :term:`token` on every device attached to the given
    user until one of them succeeds.

    .. warning::

        This originally existed for more convenient integration with the admin
        site. Its use is no longer recommended and it is not guaranteed to
        interact well with more recent features (such as throttling). Tokens
        should always be verified against specific devices.

    :param user: The user supplying the token.
    :type user: :class:`~django.contrib.auth.models.User`

    :param str token: An OTP token to verify.

    :returns: The device that accepted ``token``, if any.
    :rtype: :class:`~authentik.stages.authenticator.models.Device` or ``None``
    """
    with transaction.atomic():
        for device in devices_for_user(user, for_verify=True):
            if device.verify_token(token):
                break
        else:
            device = None

    return device


def devices_for_user(user, confirmed=True, for_verify=False):
    """
    Return an iterable of all devices registered to the given user.

    Returns an empty iterable for anonymous users.

    :param user: standard or custom user object.
    :type user: :class:`~django.contrib.auth.models.User`

    :param bool confirmed: If ``None``, all matching devices are returned.
        Otherwise, this can be any true or false value to limit the query
        to confirmed or unconfirmed devices, respectively.

    :param bool for_verify: If ``True``, we'll load the devices with
        :meth:`~django.db.models.query.QuerySet.select_for_update` to prevent
        concurrent verifications from succeeding. In which case, this must be
        called inside a transaction.

    :rtype: iterable
    """
    if user.is_anonymous:
        return

    for model in device_classes():
        device_set = model.objects.devices_for_user(user, confirmed=confirmed)
        if for_verify:
            device_set = device_set.select_for_update()

        yield from device_set


def user_has_device(user, confirmed=True):
    """
    Return ``True`` if the user has at least one device.

    Returns ``False`` for anonymous users.

    :param user: standard or custom user object.
    :type user: :class:`~django.contrib.auth.models.User`

    :param confirmed: If ``None``, all matching devices are considered.
        Otherwise, this can be any true or false value to limit the query
        to confirmed or unconfirmed devices, respectively.
    """
    try:
        next(devices_for_user(user, confirmed=confirmed))
    except StopIteration:
        has_device = False
    else:
        has_device = True

    return has_device


def device_classes():
    """
    Returns an iterable of all loaded device models.
    """
    from django.apps import apps  # isort: skip
    from authentik.stages.authenticator.models import Device

    for config in apps.get_app_configs():
        for model in config.get_models():
            if issubclass(model, Device):
                yield model
