"""Microsoft Entra Provider tasks"""

from dramatiq.actor import actor

from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.lib.sync.outgoing.tasks import SyncTasks

sync_tasks = SyncTasks(MicrosoftEntraProvider)


@actor
def microsoft_entra_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@actor
def microsoft_entra_sync(provider_pk: int, *args, **kwargs):
    """Run full sync for Microsoft Entra provider"""
    return sync_tasks.sync(provider_pk, microsoft_entra_sync_objects)


@actor
def microsoft_entra_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@actor
def microsoft_entra_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
