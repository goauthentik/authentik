"""SCIM Provider tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor

from authentik.lib.sync.outgoing.tasks import SyncTasks
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
def scim_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@actor(description=_("Dispatch syncs for a direct object (user, group) for SCIM providers."))
def scim_sync_direct_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_direct_dispatch(scim_sync_direct, *args, **kwargs)


@actor(description=_("Sync a related object (memberships) for SCIM provider."))
def scim_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)


@actor(description=_("Dispatch syncs for a related object (memberships) for SCIM providers."))
def scim_sync_m2m_dispatch(*args, **kwargs):
    return sync_tasks.sync_signal_m2m_dispatch(scim_sync_m2m, *args, **kwargs)
