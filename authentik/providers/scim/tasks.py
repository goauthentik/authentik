"""SCIM Provider tasks"""

from django.core.cache import cache
from django.db import transaction
from django.db.models import Model, Q
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from dramatiq.errors import Retry

from authentik.core.expression.exceptions import SkipObjectException
from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.exceptions import (
    BaseSyncException,
    DryRunRejected,
    NotFoundSyncException,
    StopSync,
    TransientSyncException,
)
from authentik.lib.sync.outgoing.models import OutgoingSyncProvider
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.lib.utils.reflection import class_to_path
from authentik.policies.engine import effective_policy_user
from authentik.policies.process import cache_key
from authentik.policies.types import PolicyRequest
from authentik.providers.scim.clients.groups import SCIMGroupClient
from authentik.providers.scim.models import SCIMProvider, SCIMProviderUser
from authentik.tasks.middleware import CurrentTask

sync_tasks = SyncTasks(SCIMProvider)
SCOPE_SYNC_PAGE_SIZE = 100


def _invalidate_scope_policy_cache(provider: SCIMProvider, users):
    """Invalidate only requestless decisions used by this provider's affected users."""
    bindings = list(
        provider.backchannel_application.bindings.filter(policy__isnull=False).only("pk")
    )
    if not bindings:
        return
    requests = {
        effective.pk: PolicyRequest(effective)
        for user in users.only("pk", "type")
        for effective in (effective_policy_user(user),)
    }
    cache.delete_many(
        [cache_key(binding, request) for binding in bindings for request in requests.values()]
    )


@actor(description=_("Reconcile a page of SCIM application access changes."))
def scim_sync_scope(provider_pk: int, user_pks: list[int]):
    """Reconcile current access without discovering or rewriting managed users."""
    provider = (
        SCIMProvider.objects.filter(pk=provider_pk, backchannel_application__isnull=False)
        .select_related("backchannel_application")
        .first()
    )
    if not provider:
        return
    users = User.objects.filter(pk__in=user_pks).exclude_anonymous()
    _invalidate_scope_policy_cache(provider, users)
    in_scope = set(
        provider.get_object_qs(User, pk__in=user_pks, use_cache=False).values_list("pk", flat=True)
    )
    mapped = set(
        SCIMProviderUser.objects.filter(provider=provider, user_id__in=user_pks).values_list(
            "user_id", flat=True
        )
    )
    changed = in_scope ^ mapped
    if not changed:
        return
    task = CurrentTask.get_task()
    try:
        client = provider.client_for_model(User)
        for user in users.filter(pk__in=changed).iterator():
            try:
                with client.object_lock(user):
                    allowed = provider.get_object_qs(User, pk=user.pk, use_cache=False).exists()
                    connection = SCIMProviderUser.objects.filter(
                        provider=provider, user=user
                    ).first()
                    if allowed:
                        if connection is None:
                            with transaction.atomic():
                                connection, created = client.write(user)
                                if connection is not None and created:
                                    _queue_user_memberships(user, provider)
                    elif connection is not None:
                        try:
                            client.delete(connection.scim_id)
                        except NotFoundSyncException:
                            pass
            except SkipObjectException:
                continue
            except DryRunRejected:
                continue
            except TransientSyncException:
                raise
            except BaseSyncException as exc:
                task.warning(exc.detail())
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
