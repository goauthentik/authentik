"""Kerberos Sync tasks"""

from django.core.cache import cache
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.utils.errors import exception_to_string
from authentik.sources.kerberos.models import KerberosSource
from authentik.sources.kerberos.sync import KerberosSync
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task, TaskStatus

LOGGER = get_logger()
CACHE_KEY_STATUS = "goauthentik.io/sources/kerberos/status/"


@actor
def kerberos_connectivity_check(pk: str):
    """Check connectivity for Kerberos Sources"""
    # 2 hour timeout, this task should run every hour
    timeout = 60 * 60 * 2
    source = KerberosSource.objects.filter(enabled=True, pk=pk).first()
    if not source:
        return
    status = source.check_connection()
    cache.set(CACHE_KEY_STATUS + source.slug, status, timeout=timeout)


@actor(time_limit=(60 * 60 * CONFIG.get_int("sources.kerberos.task_timeout_hours")) * 2.5 * 1000)
def kerberos_sync(pk: str):
    """Sync a single source"""
    self: Task = CurrentTask.get_task()
    source: KerberosSource = KerberosSource.objects.filter(enabled=True, pk=pk).first()
    if not source:
        return
    try:
        with source.sync_lock as lock_acquired:
            if not lock_acquired:
                LOGGER.debug(
                    "Failed to acquire lock for Kerberos sync, skipping task", source=source.slug
                )
                return
            syncer = KerberosSync(source)
            syncer.sync()
            self.set_status(TaskStatus.SUCCESSFUL, *syncer.messages)
    except StopSync as exc:
        LOGGER.warning(exception_to_string(exc))
        self.set_error(exc)
