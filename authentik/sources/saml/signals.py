"""authentik saml source signal listener"""
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.models import USER_ATTRIBUTE_DELETE_ON_LOGOUT, User

LOGGER = get_logger()


@receiver(user_logged_out)
def on_user_logged_out(sender, request: HttpRequest, user: User, **_):
    """Delete temporary user if the `delete_on_logout` flag is enabled"""
    if not user:
        return
    if user.attributes.get(USER_ATTRIBUTE_DELETE_ON_LOGOUT, False):
        LOGGER.debug("Deleted temporary user", user=user)
        user.delete()
