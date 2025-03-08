"""Microsoft Entra Provider tasks"""

from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.lib.sync.outgoing.exceptions import TransientSyncException
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.tasks.tasks import TaskData, task

sync_tasks = SyncTasks(MicrosoftEntraProvider)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def microsoft_entra_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@task(bind=True, autoretry_for=(TransientSyncException,), retry_backoff=True)
def microsoft_entra_sync(self: TaskData, provider_pk: int, *args, **kwargs):
    """Run full sync for Microsoft Entra provider"""
    return sync_tasks.sync_single(self, provider_pk, microsoft_entra_sync_objects)


@task()
def microsoft_entra_sync_all():
    return sync_tasks.sync_all(microsoft_entra_sync)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def microsoft_entra_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def microsoft_entra_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
