"""SCIM Provider tasks"""

from authentik.common.sync.outgoing.exceptions import TransientSyncException
from authentik.common.sync.outgoing.tasks import SyncTasks
from authentik.events.system_tasks import SystemTask
from authentik.providers.scim.models import SCIMProvider
from authentik.root.celery import CELERY_APP

sync_tasks = SyncTasks(SCIMProvider)


@CELERY_APP.task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def scim_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@CELERY_APP.task(
    base=SystemTask, bind=True, autoretry_for=(TransientSyncException,), retry_backoff=True
)
def scim_sync(self, provider_pk: int, *args, **kwargs):
    """Run full sync for SCIM provider"""
    return sync_tasks.sync_single(self, provider_pk, scim_sync_objects)


@CELERY_APP.task()
def scim_sync_all():
    return sync_tasks.sync_all(scim_sync)


@CELERY_APP.task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def scim_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@CELERY_APP.task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def scim_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
