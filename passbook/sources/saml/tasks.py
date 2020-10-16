"""passbook saml source tasks"""
from django.utils.timezone import now
from structlog import get_logger

from passbook.core.models import User
from passbook.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from passbook.lib.utils.time import timedelta_from_string
from passbook.root.celery import CELERY_APP
from passbook.sources.saml.models import SAMLSource

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=MonitoredTask)
def clean_temporary_users(self: MonitoredTask):
    """Remove old temporary users"""
    _now = now()
    messages = []
    deleted_users = 0
    for user in User.objects.filter(attributes__saml__isnull=False):
        sources = SAMLSource.objects.filter(
            pk=user.attributes.get("saml", {}).get("source", "")
        )
        if not sources.exists():
            LOGGER.warning(
                "User has an invalid SAML Source and won't be deleted!", user=user
            )
            messages.append(
                f"User {user} has an invalid SAML Source and won't be deleted!"
            )
            continue
        source = sources.first()
        source_delta = timedelta_from_string(source.temporary_user_delete_after)
        if _now - user.last_login >= source_delta:
            LOGGER.debug(
                "User is expired and will be deleted.", user=user, delta=source_delta
            )
            # TODO: Check if user is signed in anywhere?
            user.delete()
            deleted_users += 1
    messages.append(f"Successfully deleted {deleted_users} users.")
    self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL, messages))
