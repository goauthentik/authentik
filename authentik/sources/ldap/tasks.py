"""LDAP Sync tasks"""
from uuid import uuid4

from celery import chain, group
from django.core.cache import cache
from ldap3.core.exceptions import LDAPException
from structlog.stdlib import get_logger

from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.lib.config import CONFIG
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.reflection import class_to_path, path_to_class
from authentik.root.celery import CELERY_APP
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer

LOGGER = get_logger()
SYNC_CLASSES = [
    UserLDAPSynchronizer,
    GroupLDAPSynchronizer,
    MembershipLDAPSynchronizer,
]
CACHE_KEY_PREFIX = "goauthentik.io/sources/ldap/page/"


@CELERY_APP.task()
def ldap_sync_all():
    """Sync all sources"""
    for source in LDAPSource.objects.filter(enabled=True):
        ldap_sync_single(source.pk)


@CELERY_APP.task()
def ldap_sync_single(source_pk: str):
    """Sync a single source"""
    source: LDAPSource = LDAPSource.objects.filter(pk=source_pk).first()
    if not source:
        return
    task = chain(
        # User and group sync can happen at once, they have no dependencies on each other
        group(
            ldap_sync_paginator(source, UserLDAPSynchronizer)
            + ldap_sync_paginator(source, GroupLDAPSynchronizer),
        ),
        # Membership sync needs to run afterwards
        group(
            ldap_sync_paginator(source, MembershipLDAPSynchronizer),
        ),
    )
    task()


def ldap_sync_paginator(source: LDAPSource, sync: type[BaseLDAPSynchronizer]) -> list:
    """Return a list of task signatures with LDAP pagination data"""
    sync_inst: BaseLDAPSynchronizer = sync(source)
    signatures = []
    for page in sync_inst.get_objects():
        page_cache_key = CACHE_KEY_PREFIX + str(uuid4())
        cache.set(page_cache_key, page)
        page_sync = ldap_sync.si(source.pk, class_to_path(sync), page_cache_key)
        signatures.append(page_sync)
    return signatures


@CELERY_APP.task(
    bind=True,
    base=MonitoredTask,
    soft_time_limit=60 * 60 * int(CONFIG.y("ldap.task_timeout_hours")),
    task_time_limit=60 * 60 * int(CONFIG.y("ldap.task_timeout_hours")),
)
def ldap_sync(self: MonitoredTask, source_pk: str, sync_class: str, page_cache_key: str):
    """Synchronization of an LDAP Source"""
    self.result_timeout_hours = int(CONFIG.y("ldap.task_timeout_hours"))
    source: LDAPSource = LDAPSource.objects.filter(pk=source_pk).first()
    if not source:
        # Because the source couldn't be found, we don't have a UID
        # to set the state with
        return
    sync: type[BaseLDAPSynchronizer] = path_to_class(sync_class)
    uid = page_cache_key.replace(CACHE_KEY_PREFIX, "")
    self.set_uid(f"{source.slug}:{sync.name()}:{uid}")
    try:
        sync_inst: BaseLDAPSynchronizer = sync(source)
        page = cache.get(page_cache_key)
        if not page:
            return
        cache.touch(page_cache_key)
        count = sync_inst.sync(page)
        messages = sync_inst.messages
        messages.append(f"Synced {count} objects.")
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL,
                messages,
            )
        )
        cache.delete(page_cache_key)
    except LDAPException as exc:
        # No explicit event is created here as .set_status with an error will do that
        LOGGER.warning(exception_to_string(exc))
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
