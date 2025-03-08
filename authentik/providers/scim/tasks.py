"""SCIM Provider tasks"""

from authentik.lib.sync.outgoing.exceptions import TransientSyncException
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.providers.scim.models import SCIMProvider
from authentik.tasks.tasks import task

sync_tasks = SyncTasks(SCIMProvider)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def scim_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@task(bind=True, autoretry_for=(TransientSyncException,), retry_backoff=True)
def scim_sync(self, provider_pk: int, *args, **kwargs):
    """Run full sync for SCIM provider"""
    return sync_tasks.sync_single(self, provider_pk, scim_sync_objects)


@task()
def scim_sync_all():
    return sync_tasks.sync_all(scim_sync)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def scim_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def scim_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
