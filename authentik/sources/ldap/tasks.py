"""LDAP Sync tasks"""

from uuid import uuid4

from celery import chain, group
from django.core.cache import cache
from ldap3.core.exceptions import LDAPException
from structlog.stdlib import get_logger

from authentik.events.models import SystemTask as DBSystemTask
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.lib.config import CONFIG
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.utils.reflection import class_to_path, path_to_class
from authentik.root.celery import CELERY_APP
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.sources.ldap.sync.forward_delete_groups import GroupLDAPForwardDeletion
from authentik.sources.ldap.sync.forward_delete_users import UserLDAPForwardDeletion
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
CACHE_KEY_STATUS = "goauthentik.io/sources/ldap/status/"


@CELERY_APP.task()
def ldap_sync_all():
    """Sync all sources"""
    for source in LDAPSource.objects.filter(enabled=True):
        ldap_sync_single.apply_async(args=[str(source.pk)])


@CELERY_APP.task()
def ldap_connectivity_check(pk: str | None = None):
    """Check connectivity for LDAP Sources"""
    # 2 hour timeout, this task should run every hour
    timeout = 60 * 60 * 2
    sources = LDAPSource.objects.filter(enabled=True)
    if pk:
        sources = sources.filter(pk=pk)
    for source in sources:
        status = source.check_connection()
        cache.set(CACHE_KEY_STATUS + source.slug, status, timeout=timeout)


@CELERY_APP.task(
    # We take the configured hours timeout time by 3.5 as we run user and
    # group in parallel and then membership, then deletions, so 3x is to cover the serial tasks,
    # and 0.5x on top of that to give some more leeway
    soft_time_limit=(60 * 60 * CONFIG.get_int("ldap.task_timeout_hours")) * 3.5,
    task_time_limit=(60 * 60 * CONFIG.get_int("ldap.task_timeout_hours")) * 3.5,
)
def ldap_sync_single(source_pk: str):
    """Sync a single source"""
    source: LDAPSource = LDAPSource.objects.filter(pk=source_pk).first()
    if not source:
        return
    with source.sync_lock as lock_acquired:
        if not lock_acquired:
            LOGGER.debug("Failed to acquire lock for LDAP sync, skipping task", source=source.slug)
            return
        # Delete all sync tasks from the cache
        DBSystemTask.objects.filter(name="ldap_sync", uid__startswith=source.slug).delete()

        # The order of these operations needs to be preserved as each depends on the previous one(s)
        # 1. User and group sync can happen simultaneously
        # 2. Membership sync needs to run afterwards
        # 3. Finally, user and group deletions can happen simultaneously
        user_group_sync = ldap_sync_paginator(source, UserLDAPSynchronizer) + ldap_sync_paginator(
            source, GroupLDAPSynchronizer
        )
        membership_sync = ldap_sync_paginator(source, MembershipLDAPSynchronizer)
        user_group_deletion = ldap_sync_paginator(
            source, UserLDAPForwardDeletion
        ) + ldap_sync_paginator(source, GroupLDAPForwardDeletion)

        # Celery is buggy with empty groups, so we are careful only to add non-empty groups.
        # See https://github.com/celery/celery/issues/9772
        task_groups = []
        if user_group_sync:
            task_groups.append(group(user_group_sync))
        if membership_sync:
            task_groups.append(group(membership_sync))
        if user_group_deletion:
            task_groups.append(group(user_group_deletion))

        all_tasks = chain(task_groups)
        all_tasks()


def ldap_sync_paginator(source: LDAPSource, sync: type[BaseLDAPSynchronizer]) -> list:
    """Return a list of task signatures with LDAP pagination data"""
    sync_inst: BaseLDAPSynchronizer = sync(source)
    signatures = []
    for page in sync_inst.get_objects():
        page_cache_key = CACHE_KEY_PREFIX + str(uuid4())
        cache.set(page_cache_key, page, 60 * 60 * CONFIG.get_int("ldap.task_timeout_hours"))
        page_sync = ldap_sync.si(str(source.pk), class_to_path(sync), page_cache_key)
        signatures.append(page_sync)
    return signatures


@CELERY_APP.task(
    bind=True,
    base=SystemTask,
    soft_time_limit=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours"),
    task_time_limit=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours"),
)
def ldap_sync(self: SystemTask, source_pk: str, sync_class: str, page_cache_key: str):
    """Synchronization of an LDAP Source"""
    self.result_timeout_hours = CONFIG.get_int("ldap.task_timeout_hours")
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
            error_message = (
                f"Could not find page in cache: {page_cache_key}. "
                + "Try increasing ldap.task_timeout_hours"
            )
            LOGGER.warning(error_message)
            self.set_status(TaskStatus.ERROR, error_message)
            return
        cache.touch(page_cache_key)
        count = sync_inst.sync(page)
        messages = sync_inst.messages
        messages.append(f"Synced {count} objects.")
        self.set_status(
            TaskStatus.SUCCESSFUL,
            *messages,
        )
        cache.delete(page_cache_key)
    except (LDAPException, StopSync) as exc:
        # No explicit event is created here as .set_status with an error will do that
        LOGGER.warning("Failed to sync LDAP", exc=exc, source=source)
        self.set_error(exc)
