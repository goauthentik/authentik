"""LDAP Sync tasks"""

from uuid import uuid4

from django.core.cache import cache
from dramatiq.actor import actor
from dramatiq.composition import group
from ldap3.core.exceptions import LDAPException
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.utils.errors import exception_to_string
from authentik.lib.utils.reflection import class_to_path, path_to_class
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task, TaskStatus

LOGGER = get_logger()
SYNC_CLASSES = [
    UserLDAPSynchronizer,
    GroupLDAPSynchronizer,
    MembershipLDAPSynchronizer,
]
CACHE_KEY_PREFIX = "goauthentik.io/sources/ldap/page/"
CACHE_KEY_STATUS = "goauthentik.io/sources/ldap/status/"


@actor
def ldap_connectivity_check(source_pk: str):
    """Check connectivity for LDAP Sources"""
    # 2 hour timeout, this task should run every hour
    timeout = 60 * 60 * 2
    source = LDAPSource.objects.filter(enabled=True, pk=source_pk).first()
    if not source:
        return
    status = source.check_connection()
    cache.set(CACHE_KEY_STATUS + source.slug, status, timeout=timeout)


# We take the configured hours timeout time by 2.5 as we run user and
# group in parallel and then membership, so 2x is to cover the serial tasks,
# and 0.5x on top of that to give some more leeway
@actor(time_limit=(60 * 60 * CONFIG.get_int("ldap.task_timeout_hours")) * 2.5 * 1000)
def ldap_sync(source_pk: str):
    """Sync a single source"""
    self: Task = CurrentTask.get_task()
    source: LDAPSource = LDAPSource.objects.filter(pk=source_pk).first()
    if not source:
        return
    # Don't sync sources when they don't have any property mappings. This will only happen if:
    # - the user forgets to set them or
    # - the source is newly created, the mappings are save a bit later, which might cause invalid
    #   data
    if source.sync_users and not source.user_property_mappings.exists():
        # TODO: add to task messages
        LOGGER.warning(
            "LDAP source has user sync enabled but does not have user property mappings configured, not syncing",  # noqa: E501
            source=source.slug,
        )
        return
    if source.sync_groups and not source.group_property_mappings.exists():
        # TODO: add to task messages
        LOGGER.warning(
            "LDAP source has group sync enabled but does not have group property mappings configured, not syncing",  # noqa: E501
            source=source.slug,
        )
        return
    with source.sync_lock as lock_acquired:
        if not lock_acquired:
            LOGGER.debug("Failed to acquire lock for LDAP sync, skipping task", source=source.slug)
            return
        # User and group sync can happen at once, they have no dependencies on each other
        task_users_group = group(
            ldap_sync_paginator(source, UserLDAPSynchronizer, schedule_uid=self.schedule_uid)
            + ldap_sync_paginator(source, GroupLDAPSynchronizer, schedule_uid=self.schedule_uid),
        )
        task_users_group.run()
        task_users_group.wait(timeout=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000)
        # Membership sync needs to run afterwards
        task_membership = group(
            ldap_sync_paginator(source, MembershipLDAPSynchronizer, schedule_uid=self.schedule_uid),
        )
        task_membership.run()
        task_membership.wait(timeout=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000)


def ldap_sync_paginator(source: LDAPSource, sync: type[BaseLDAPSynchronizer], **options) -> list:
    """Return a list of task signatures with LDAP pagination data"""
    sync_inst: BaseLDAPSynchronizer = sync(source)
    tasks = []
    for page in sync_inst.get_objects():
        page_cache_key = CACHE_KEY_PREFIX + str(uuid4())
        cache.set(page_cache_key, page, 60 * 60 * CONFIG.get_int("ldap.task_timeout_hours"))
        page_sync = ldap_sync_page.message_with_options(
            args=(source.pk, class_to_path(sync), page_cache_key),
            **options,
        )
        tasks.append(page_sync)
    return tasks


@actor(time_limit=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000)
def ldap_sync_page(source_pk: str, sync_class: str, page_cache_key: str):
    """Synchronization of an LDAP Source"""
    self: Task = CurrentTask.get_task()
    # self.result_timeout_hours = CONFIG.get_int("ldap.task_timeout_hours")
    source: LDAPSource = LDAPSource.objects.filter(pk=source_pk).first()
    if not source:
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
        LOGGER.warning(exception_to_string(exc))
        self.set_error(exc)
