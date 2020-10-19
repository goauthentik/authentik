"""LDAP Sync tasks"""
from time import time

from django.core.cache import cache
from django.utils.text import slugify
from ldap3.core.exceptions import LDAPException

from passbook.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from passbook.root.celery import CELERY_APP
from passbook.sources.ldap.models import LDAPSource
from passbook.sources.ldap.sync import LDAPSynchronizer


@CELERY_APP.task()
def ldap_sync_all():
    """Sync all sources"""
    for source in LDAPSource.objects.filter(enabled=True):
        ldap_sync.delay(source.pk)


@CELERY_APP.task(bind=True, base=MonitoredTask)
def ldap_sync(self: MonitoredTask, source_pk: int):
    """Synchronization of an LDAP Source"""
    source: LDAPSource = LDAPSource.objects.get(pk=source_pk)
    self.set_uid(slugify(source.name))
    try:
        syncer = LDAPSynchronizer(source)
        user_count = syncer.sync_users()
        group_count = syncer.sync_groups()
        syncer.sync_membership()
        cache_key = source.state_cache_prefix("last_sync")
        cache.set(cache_key, time(), timeout=60 * 60)
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL,
                [f"Synced {user_count} users", f"Synced {group_count} groups"],
            )
        )
    except LDAPException as exc:
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
