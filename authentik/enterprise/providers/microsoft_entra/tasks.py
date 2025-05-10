"""Microsoft Entra Provider tasks"""

from authentik.common.sync.outgoing.exceptions import TransientSyncException
from authentik.common.sync.outgoing.tasks import SyncTasks
from authentik.enterprise.providers.microsoft_entra.models import MicrosoftEntraProvider
from authentik.events.system_tasks import SystemTask
from authentik.root.celery import CELERY_APP

sync_tasks = SyncTasks(MicrosoftEntraProvider)


@CELERY_APP.task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def microsoft_entra_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@CELERY_APP.task(
    base=SystemTask, bind=True, autoretry_for=(TransientSyncException,), retry_backoff=True
)
def microsoft_entra_sync(self, provider_pk: int, *args, **kwargs):
    """Run full sync for Microsoft Entra provider"""
    return sync_tasks.sync_single(self, provider_pk, microsoft_entra_sync_objects)


@CELERY_APP.task()
def microsoft_entra_sync_all():
    return sync_tasks.sync_all(microsoft_entra_sync)


@CELERY_APP.task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def microsoft_entra_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@CELERY_APP.task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def microsoft_entra_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
