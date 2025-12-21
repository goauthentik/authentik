"""Kerberos Sync tasks"""

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.sync.incoming.models import SyncOutgoingTriggerMode
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.sync.outgoing.signals import sync_outgoing_inhibit_dispatch
from authentik.lib.utils.reflection import all_subclasses
from authentik.sources.kerberos.models import KerberosSource
from authentik.sources.kerberos.sync import KerberosSync
from authentik.tasks.middleware import CurrentTask

LOGGER = get_logger()
CACHE_KEY_STATUS = "goauthentik.io/sources/kerberos/status/"


@actor(description=_("Check connectivity for Kerberos sources."))
def kerberos_connectivity_check(pk: str):
    """Check connectivity for Kerberos Sources"""
    # 2 hour timeout, this task should run every hour
    timeout = 60 * 60 * 2
    source = KerberosSource.objects.filter(enabled=True, pk=pk).first()
    if not source:
        return
    status = source.check_connection()
    cache.set(CACHE_KEY_STATUS + source.slug, status, timeout=timeout)


@actor(
    time_limit=(60 * 60 * CONFIG.get_int("sources.kerberos.task_timeout_hours")) * 2.5 * 1000,
    description=_("Sync Kerberos source."),
)
def kerberos_sync(pk: str):
    self = CurrentTask.get_task()
    source: KerberosSource = KerberosSource.objects.filter(enabled=True, pk=pk).first()
    if not source:
        return
    try:
        with source.sync_lock as lock_acquired:
            if not lock_acquired:
                self.info("Synchronization is already running. Skipping")
                LOGGER.debug(
                    "Failed to acquire lock for Kerberos sync, skipping task", source=source.slug
                )
                return
            syncer = KerberosSync(source, self)
            if source.sync_outgoing_trigger_mode == SyncOutgoingTriggerMode.IMMEDIATE:
                syncer.sync()
            else:
                with sync_outgoing_inhibit_dispatch():
                    syncer.sync()
        if source.sync_outgoing_trigger_mode == SyncOutgoingTriggerMode.DEFERRED_END:
            for outgoing_sync_provider_cls in all_subclasses(OutgoingSyncProvider):
                for provider in outgoing_sync_provider_cls.objects.all():
                    provider.sync_dispatch()
    except StopSync as exc:
        LOGGER.warning("Error syncing kerberos", exc=exc, source=source)
        self.error(exc)
        raise exc
