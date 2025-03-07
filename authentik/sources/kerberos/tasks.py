"""Kerberos Sync tasks"""

from django.core.cache import cache
from structlog.stdlib import get_logger

from authentik.events.models import SystemTask as DBSystemTask
from authentik.events.models import TaskStatus
from authentik.lib.config import CONFIG
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.utils.errors import exception_to_string
from authentik.sources.kerberos.models import KerberosSource
from authentik.sources.kerberos.sync import KerberosSync
from authentik.tasks.tasks import TaskData, async_iter, task

LOGGER = get_logger()
CACHE_KEY_STATUS = "goauthentik.io/sources/kerberos/status/"


@task()
def kerberos_sync_all():
    """Sync all sources"""
    async_iter(
        "authentik.sources.kerberos.tasks.kerberos_sync_single",
        KerberosSource.objects.filter(enabled=True, sync_users=True).values_list("pk", flat=True),
    )


@task()
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


@task(
    bind=True,
    # We take the configured hours timeout time by 2.5 as we run user and
    # group in parallel and then membership, so 2x is to cover the serial tasks,
    # and 0.5x on top of that to give some more leeway
    timeout=(60 * 60 * CONFIG.get_int("sources.kerberos.task_timeout_hours")) * 2.5,
)
def kerberos_sync_single(self: TaskData, source_pk: str):
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
