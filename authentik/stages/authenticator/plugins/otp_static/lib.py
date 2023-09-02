from django.contrib.auth import get_user_model

from .models import StaticDevice, StaticToken


def add_static_token(username, token=None):
    """
    Adds a random static token to the identified user.

    This is the implementation for the management command of a similar name.
    Returns the StaticToken object created.

    """
    user = get_user_model().objects.get_by_natural_key(username)

    device = StaticDevice.objects.filter(user=user).first()
    if device is None:
        device = StaticDevice.objects.create(user=user, name="Backup Code")

    if token is None:
        token = StaticToken.random_token()

    return device.token_set.create(token=token)
