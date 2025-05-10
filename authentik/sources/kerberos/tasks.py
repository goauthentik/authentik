"""Kerberos Sync tasks"""

from django.core.cache import cache
from structlog.stdlib import get_logger

from authentik.common.config import CONFIG
from authentik.common.sync.outgoing.exceptions import StopSync
from authentik.common.utils.errors import exception_to_string
from authentik.events.models import SystemTask as DBSystemTask
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.root.celery import CELERY_APP
from authentik.sources.kerberos.models import KerberosSource
from authentik.sources.kerberos.sync import KerberosSync

LOGGER = get_logger()
CACHE_KEY_STATUS = "goauthentik.io/sources/kerberos/status/"


@CELERY_APP.task()
def kerberos_sync_all():
    """Sync all sources"""
    for source in KerberosSource.objects.filter(enabled=True, sync_users=True):
        kerberos_sync_single.delay(str(source.pk))


@CELERY_APP.task()
def kerberos_connectivity_check(pk: str | None = None):
    """Check connectivity for Kerberos Sources"""
    # 2 hour timeout, this task should run every hour
    timeout = 60 * 60 * 2
    sources = KerberosSource.objects.filter(enabled=True)
    if pk:
        sources = sources.filter(pk=pk)
    for source in sources:
        status = source.check_connection()
        cache.set(CACHE_KEY_STATUS + source.slug, status, timeout=timeout)


@CELERY_APP.task(
    bind=True,
    base=SystemTask,
    # We take the configured hours timeout time by 2.5 as we run user and
    # group in parallel and then membership, so 2x is to cover the serial tasks,
    # and 0.5x on top of that to give some more leeway
    soft_time_limit=(60 * 60 * CONFIG.get_int("sources.kerberos.task_timeout_hours")) * 2.5,
    task_time_limit=(60 * 60 * CONFIG.get_int("sources.kerberos.task_timeout_hours")) * 2.5,
)
def kerberos_sync_single(self, source_pk: str):
    """Sync a single source"""
    source: KerberosSource = KerberosSource.objects.filter(pk=source_pk).first()
    if not source or not source.enabled:
        return
    try:
        with source.sync_lock as lock_acquired:
            if not lock_acquired:
                LOGGER.debug(
                    "Failed to acquire lock for Kerberos sync, skipping task", source=source.slug
                )
                return
            # Delete all sync tasks from the cache
            DBSystemTask.objects.filter(name="kerberos_sync", uid__startswith=source.slug).delete()
            syncer = KerberosSync(source)
            syncer.sync()
            self.set_status(TaskStatus.SUCCESSFUL, *syncer.messages)
    except StopSync as exc:
        LOGGER.warning(exception_to_string(exc))
        self.set_error(exc)
