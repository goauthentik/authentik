"""SCIM Provider tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor

from authentik.core.models import Group, User
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.lib.utils.reflection import class_to_path
from authentik.providers.scim.models import SCIMProvider

sync_tasks = SyncTasks(SCIMProvider)


@actor(description=_("Sync SCIM provider objects."))
def scim_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@actor(description=_("Full sync for SCIM provider."))
def scim_sync(provider_pk: int, *args, **kwargs):
    """Run full sync for SCIM provider"""
    return sync_tasks.sync(provider_pk, scim_sync_objects)


@actor(description=_("Sync a direct object (user, group) for SCIM provider."))
def scim_sync_direct(model: str, pk: str | int, provider_pk: int):
    written = sync_tasks.sync_signal_direct(model, pk, provider_pk)
    if not written or model != class_to_path(User):
        return
    provider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider or provider.dry_run:
        return
    # A membership task can run before the user's remote ID is available and silently
    # omit it. Reconcile current memberships after the user write has committed and
    # released its lock. Repeat this on updates too, so a retry after an interrupted
    # dispatch repairs memberships even when the user connection already exists.
    for group_pk in provider.get_object_qs(Group, users__pk=pk).values_list("pk", flat=True):
        scim_sync_direct.send_with_options(
            args=(class_to_path(Group), group_pk, provider.pk),
            rel_obj=provider,
            uid=f"{provider.name}:group:{group_pk}:direct",
        )


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
