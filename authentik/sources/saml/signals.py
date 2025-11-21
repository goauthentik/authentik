"""authentik saml source signal listener"""

from hashlib import sha256

from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.models import (
    USER_ATTRIBUTE_DELETE_ON_LOGOUT,
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_TRANSIENT_TOKEN,
    User,
)

LOGGER = get_logger()


@receiver(user_logged_out)
def on_user_logged_out(sender, request: HttpRequest, user: User, **_):
    """Delete temporary user if the `delete_on_logout` flag is enabled"""
    if not user:
        return
    transient_name_id = user.attributes.get(USER_ATTRIBUTE_TRANSIENT_TOKEN)
    if transient_name_id == sha256(user.username.encode("utf-8")).hexdigest():
        LOGGER.debug("Deleted temporary user", user=user)
        user.delete()
        return
    if transient_name_id is not None:
        LOGGER.debug("Deleted transient user attributes", user=user)
        user.attributes.pop(USER_ATTRIBUTE_TRANSIENT_TOKEN, None)
        user.attributes.pop(USER_ATTRIBUTE_EXPIRES, None)
        user.save()

    if user.attributes.get(USER_ATTRIBUTE_DELETE_ON_LOGOUT, False):
        LOGGER.debug("Deleted temporary user", user=user)
        user.delete()
