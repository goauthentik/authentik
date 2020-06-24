"""passbook saml source tasks"""
from django.utils.timezone import now
from structlog import get_logger

from passbook.core.models import User
from passbook.providers.saml.utils.time import timedelta_from_string
from passbook.root.celery import CELERY_APP
from passbook.sources.saml.models import SAMLSource

LOGGER = get_logger()


@CELERY_APP.task()
def clean_temporary_users():
    """Remove old temporary users"""
    _now = now()
    for user in User.objects.filter(attributes__saml__isnull=False):
        sources = SAMLSource.objects.filter(
            pk=user.attributes.get("saml", {}).get("source", "")
        )
        if not sources.exists():
            LOGGER.warning(
                "User has an invalid SAML Source and won't be deleted!", user=user
            )
        source = sources.first()
        source_delta = timedelta_from_string(source.temporary_user_delete_after)
        if _now - user.last_login >= source_delta:
            LOGGER.debug(
                "User is expired and will be deleted.", user=user, delta=source_delta
            )
            user.delete()
