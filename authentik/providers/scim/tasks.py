"""SCIM Provider tasks"""

from dramatiq.actor import actor

from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.providers.scim.models import SCIMProvider

sync_tasks = SyncTasks(SCIMProvider)


@actor
def scim_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@actor
def scim_sync(provider_pk: int, *args, **kwargs):
    """Run full sync for SCIM provider"""
    return sync_tasks.sync(provider_pk, scim_sync_objects)


@actor
def scim_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@actor
def scim_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
