"""passbook saml source signal listener"""
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest
from structlog import get_logger

from passbook.core.models import User

LOGGER = get_logger()


@receiver(user_logged_out)
# pylint: disable=unused-argument
def on_user_logged_out(sender, request: HttpRequest, user: User, **_):
    """Delete temporary user if the `delete_on_logout` flag is enabled"""
    if "saml" in user.attributes:
        if "delete_on_logout" in user.attributes["saml"]:
            if user.attributes["saml"]["delete_on_logout"]:
                LOGGER.debug("Deleted temporary user", user=user)
                user.delete()
