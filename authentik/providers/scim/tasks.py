"""SCIM Provider tasks"""

from itertools import batched

from django.db import transaction
from django.db.models import Model, Q
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from dramatiq.errors import Retry

from authentik.core.expression.exceptions import SkipObjectException
from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.exceptions import (
    DryRunRejected,
    StopSync,
    TransientSyncException,
)
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.lib.utils.reflection import class_to_path
from authentik.providers.scim.clients.groups import SCIMGroupClient
from authentik.providers.scim.models import SCIMProvider
from authentik.providers.scim.reconciliation import (
    providers_for_groups,
    providers_for_targets,
    reconcile_scope,
    users_for_group_subtrees,
    users_with_mirror_dependents,
)
from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task, TaskStatus

sync_tasks = SyncTasks(SCIMProvider)
SCOPE_SYNC_PAGE_SIZE = 100


def queue_scope_for_targets(target_pks):
    """Coalesce queued sweeps while locking their consumption until access changes commit."""
    with transaction.atomic():
        providers = providers_for_targets(target_pks).order_by("pk").select_for_update(of=("self",))
        for provider in providers:
            uid = f"{provider.pk}:scope"
            pending = Task.objects.select_for_update().filter(
                actor_name=scim_sync_scope_dispatch.actor_name,
                _uid=uid,
                state=TaskStatus.QUEUED,
            )
            if not pending.exists():
                scim_sync_scope_dispatch.send_with_options(
                    args=(provider.pk,), rel_obj=provider, uid=uid
                )


def _queue_scope_for_users(provider: SCIMProvider, user_pks):
    """Stream affected users and their transitive MIRROR actors into bounded jobs."""
    for roots in batched(user_pks, SCOPE_SYNC_PAGE_SIZE, strict=False):
        affected = users_with_mirror_dependents(roots)
        for page in batched(
            affected.values_list("pk", flat=True).iterator(), SCOPE_SYNC_PAGE_SIZE, strict=False
        ):
            scim_sync_scope.send_with_options(
                args=(provider.pk, list(page)),
                rel_obj=provider,
                uid=f"{provider.pk}:scope:{page[0]}",
            )


def queue_scope_for_membership(group_pks, user_pks):
    """Schedule access reconciliation for a membership change."""
    for provider in providers_for_groups(group_pks):
        _queue_scope_for_users(provider, user_pks)


def queue_scope_for_parentage(parent_pks, child_pks):
    """Schedule access reconciliation for users in the affected child subtrees."""
    users = users_for_group_subtrees(child_pks)
    for provider in providers_for_groups(parent_pks):
        _queue_scope_for_users(provider, users.iterator())


def queue_cleared_memberships(instance_pk: int, related_pks, reverse: bool):
    """Dispatch removed memberships in bounded jobs after their pre-clear capture."""
    for page in batched(related_pks, SCOPE_SYNC_PAGE_SIZE, strict=False):
        scim_sync_m2m_dispatch.send(instance_pk, "post_remove", list(page), reverse)


@actor(description=_("Reconcile a page of SCIM application access changes."))
def scim_sync_scope(provider_pk: int, user_pks: list[int]):
    """Reconcile current access without discovering or rewriting managed users."""
    try:
        reconcile_scope(
            provider_pk,
            user_pks,
            on_create=_queue_user_memberships,
            on_error=lambda exc: CurrentTask.get_task().warning(exc.detail()),
        )
    except TransientSyncException as exc:
        raise Retry() from exc


@actor(description=_("Dispatch a paged SCIM application access reconciliation."))
def scim_sync_scope_dispatch(provider_pk: int, after_pk: int = 0):
    """Walk users by primary key, with bounded messages and no count or offset query."""
    provider = (
        SCIMProvider.objects.filter(pk=provider_pk, backchannel_application__isnull=False)
        .only("pk")
        .first()
    )
    if not provider:
        return
    user_pks = list(
        User.objects.exclude_anonymous()
        .filter(pk__gt=after_pk)
        .order_by("pk")
        .values_list("pk", flat=True)[:SCOPE_SYNC_PAGE_SIZE]
    )
    if not user_pks:
        return
    with transaction.atomic():
        scim_sync_scope.send_with_options(
            args=(provider_pk, user_pks), rel_obj=provider, uid=f"{provider_pk}:scope:{user_pks[0]}"
        )
        if len(user_pks) == SCOPE_SYNC_PAGE_SIZE:
            scim_sync_scope_dispatch.send_with_options(
                args=(provider_pk, user_pks[-1]),
                rel_obj=provider,
                uid=f"{provider_pk}:scope:after:{user_pks[-1]}",
            )


@actor(description=_("Sync SCIM provider objects."))
def scim_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@actor(description=_("Full sync for SCIM provider."))
def scim_sync(provider_pk: int, *args, **kwargs):
    """Run full sync for SCIM provider"""
    return sync_tasks.sync(provider_pk, scim_sync_objects)


@actor(description=_("Sync a direct object (user, group) for SCIM provider."))
def scim_sync_direct(model: str, pk: str | int, provider_pk: int):
    sync_tasks.sync_signal_direct(
        model,
        pk,
        provider_pk,
        on_create=_queue_user_memberships if model == class_to_path(User) else None,
    )


def _queue_user_memberships(user: Model, provider: OutgoingSyncProvider):
    """The Postgres broker persists this job in the user connection's transaction."""
    scim_sync_user_memberships.send_with_options(
        args=(user.pk, provider.pk),
        rel_obj=provider,
        uid=f"{provider.name}:user:{user.pk}:memberships",
    )


@actor(description=_("Sync memberships for a newly provisioned SCIM user."))
def scim_sync_user_memberships(user_pk: int, provider_pk: int):
    task = CurrentTask.get_task()
    provider = SCIMProvider.objects.filter(
        Q(backchannel_application__isnull=False) | Q(application__isnull=False), pk=provider_pk
    ).first()
    if not provider or provider.dry_run:
        return
    if not provider.get_object_qs(User, pk=user_pk).exists():
        return
    try:
        client = SCIMGroupClient(provider)
        for group in provider.get_object_qs(Group, users__pk=user_pk).iterator():
            try:
                client.add_user_to_group(group, user_pk)
            except SkipObjectException:
                continue
            except StopSync as exc:
                task.warning(exc.detail())
    except TransientSyncException as exc:
        raise Retry() from exc
    except DryRunRejected:
        return


@actor(description=_("Dispatch syncs for a direct object (user, group) for SCIM providers."))
def scim_sync_direct_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_direct_dispatch(scim_sync_direct, *args, **kwargs)


@actor(description=_("Delete an object (user, group) for SCIM provider."))
def scim_sync_delete(*args, **kwargs):
    return sync_tasks.sync_signal_delete(*args, **kwargs)


@actor(description=_("Dispatch deletions for an object (user, group) for SCIM providers."))
def scim_sync_delete_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_delete_dispatch(scim_sync_delete, *args, **kwargs)


@actor(description=_("Sync a related object (memberships) for SCIM provider."))
def scim_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)


@actor(description=_("Dispatch syncs for a related object (memberships) for SCIM providers."))
def scim_sync_m2m_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_m2m_dispatch(scim_sync_m2m, *args, **kwargs)
