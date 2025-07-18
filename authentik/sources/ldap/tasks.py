"""LDAP Sync tasks"""

from uuid import uuid4

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from dramatiq.composition import group
from dramatiq.message import Message
from ldap3.core.exceptions import LDAPException
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.sync.outgoing.exceptions import StopSync
from authentik.lib.utils.reflection import class_to_path, path_to_class
from authentik.sources.ldap.models import LDAPSource
from authentik.sources.ldap.sync.base import BaseLDAPSynchronizer
from authentik.sources.ldap.sync.forward_delete_groups import GroupLDAPForwardDeletion
from authentik.sources.ldap.sync.forward_delete_users import UserLDAPForwardDeletion
from authentik.sources.ldap.sync.groups import GroupLDAPSynchronizer
from authentik.sources.ldap.sync.membership import MembershipLDAPSynchronizer
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.tasks.models import Task

LOGGER = get_logger()
SYNC_CLASSES = [
    UserLDAPSynchronizer,
    GroupLDAPSynchronizer,
    MembershipLDAPSynchronizer,
]
CACHE_KEY_PREFIX = "goauthentik.io/sources/ldap/page/"
CACHE_KEY_STATUS = "goauthentik.io/sources/ldap/status/"


@actor(description=_("Check connectivity for LDAP source."))
def ldap_connectivity_check(pk: str | None = None):
    """Check connectivity for LDAP Sources"""
    timeout = 60 * 60 * 2
    source = LDAPSource.objects.filter(pk=pk, enabled=True).first()
    if not source:
        return
    status = source.check_connection()
    cache.set(CACHE_KEY_STATUS + source.slug, status, timeout=timeout)


@actor(
    # We take the configured hours timeout time by 3.5 as we run user and
    # group in parallel and then membership, then deletions, so 3x is to cover the serial tasks,
    # and 0.5x on top of that to give some more leeway
    time_limit=(60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000) * 3.5,
    description=_("Sync LDAP source."),
)
def ldap_sync(source_pk: str):
    """Sync a single source"""
    task: Task = CurrentTask.get_task()
    source: LDAPSource = LDAPSource.objects.filter(pk=source_pk, enabled=True).first()
    if not source:
        return
    task.set_uid(f"{source.slug}")
    with source.sync_lock as lock_acquired:
        if not lock_acquired:
            task.info("Synchronization is already running. Skipping")
            LOGGER.debug("Failed to acquire lock for LDAP sync, skipping task", source=source.slug)
            return

        user_group_tasks = group(
            ldap_sync_paginator(task, source, UserLDAPSynchronizer)
            + ldap_sync_paginator(task, source, GroupLDAPSynchronizer)
        )

        membership_tasks = group(ldap_sync_paginator(task, source, MembershipLDAPSynchronizer))

        deletion_tasks = group(
            ldap_sync_paginator(task, source, UserLDAPForwardDeletion)
            + ldap_sync_paginator(task, source, GroupLDAPForwardDeletion),
        )

        # User and group sync can happen at once, they have no dependencies on each other
        user_group_tasks.run().wait(
            timeout=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000
        )
        # Membership sync needs to run afterwards
        membership_tasks.run().wait(
            timeout=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000
        )
        # Finally, deletions. What we'd really like to do here is something like
        # ```
        # user_identifiers = <ldap query>
        # User.objects.exclude(
        #     usersourceconnection__identifier__in=user_uniqueness_identifiers,
        # ).delete()
        # ```
        # This runs into performance issues in large installations. So instead we spread the
        # work out into three steps:
        # 1. Get every object from the LDAP source.
        # 2. Mark every object as "safe" in the database. This is quick, but any error could
        #    mean deleting users which should not be deleted, so we do it immediately, in
        #    large chunks, and only queue the deletion step afterwards.
        # 3. Delete every unmarked item. This is slow, so we spread it over many tasks in
        #    small chunks.
        deletion_tasks.run().wait(
            timeout=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000,
        )


def ldap_sync_paginator(
    task: Task, source: LDAPSource, sync: type[BaseLDAPSynchronizer]
) -> list[Message]:
    """Return a list of task signatures with LDAP pagination data"""
    sync_inst: BaseLDAPSynchronizer = sync(source, task)
    messages = []
    for page in sync_inst.get_objects():
        page_cache_key = CACHE_KEY_PREFIX + str(uuid4())
        cache.set(page_cache_key, page, 60 * 60 * CONFIG.get_int("ldap.task_timeout_hours"))
        page_sync = ldap_sync_page.message_with_options(
            args=(source.pk, class_to_path(sync), page_cache_key),
            rel_obj=task.rel_obj,
        )
        messages.append(page_sync)
    return messages


@actor(
    time_limit=60 * 60 * CONFIG.get_int("ldap.task_timeout_hours") * 1000,
    description=_("Sync page for LDAP source."),
)
def ldap_sync_page(source_pk: str, sync_class: str, page_cache_key: str):
    """Synchronization of an LDAP Source"""
    self: Task = CurrentTask.get_task()
    source: LDAPSource = LDAPSource.objects.filter(pk=source_pk).first()
    if not source:
        # Because the source couldn't be found, we don't have a UID
        # to set the state with
        return
    sync: type[BaseLDAPSynchronizer] = path_to_class(sync_class)
    uid = page_cache_key.replace(CACHE_KEY_PREFIX, "")
    self.set_uid(f"{source.slug}:{sync.name()}:{uid}")
    try:
        sync_inst: BaseLDAPSynchronizer = sync(source, self)
        page = cache.get(page_cache_key)
        if not page:
            error_message = (
                f"Could not find page in cache: {page_cache_key}. "
                + "Try increasing ldap.task_timeout_hours"
            )
            LOGGER.warning(error_message)
            self.error(error_message)
            return
        cache.touch(page_cache_key)
        count = sync_inst.sync(page)
        self.info(f"Synced {count} objects.")
        cache.delete(page_cache_key)
    except (LDAPException, StopSync) as exc:
        # No explicit event is created here as .error will do that
        LOGGER.warning("Failed to sync LDAP", exc=exc, source=source)
        self.error(exc)
        raise exc
