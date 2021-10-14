"""authentik saml source tasks"""
from django.utils.timezone import now
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.lib.utils.time import timedelta_from_string
from authentik.root.celery import CELERY_APP
from authentik.sources.saml.models import SAMLSource

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task()
def clean_temporary_users(self: MonitoredTask):
    """Remove temporary users created by SAML Sources"""
    _now = now()
    messages = []
    deleted_users = 0
    for user in User.objects.filter(attributes__saml__isnull=False):
        sources = SAMLSource.objects.filter(pk=user.attributes.get("saml", {}).get("source", ""))
        if not sources.exists():
            LOGGER.warning("User has an invalid SAML Source and won't be deleted!", user=user)
            messages.append(f"User {user} has an invalid SAML Source and won't be deleted!")
            continue
        source = sources.first()
        source_delta = timedelta_from_string(source.temporary_user_delete_after)
        if (
            _now - user.last_login >= source_delta
            and not AuthenticatedSession.objects.filter(user=user).exists()
        ):
            LOGGER.debug("User is expired and will be deleted.", user=user, delta=source_delta)
            user.delete()
            deleted_users += 1
    messages.append(f"Successfully deleted {deleted_users} users.")
    self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL, messages))
