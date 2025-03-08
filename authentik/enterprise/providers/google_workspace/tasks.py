"""Google Provider tasks"""

from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.lib.sync.outgoing.exceptions import TransientSyncException
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.tasks.tasks import TaskData, task

sync_tasks = SyncTasks(GoogleWorkspaceProvider)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def google_workspace_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@task(bind=True, autoretry_for=(TransientSyncException,), retry_backoff=True)
def google_workspace_sync(self: TaskData, provider_pk: int, *args, **kwargs):
    """Run full sync for Google Workspace provider"""
    return sync_tasks.sync_single(self, provider_pk, google_workspace_sync_objects)


@task()
def google_workspace_sync_all():
    return sync_tasks.sync_all(google_workspace_sync)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def google_workspace_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@task(autoretry_for=(TransientSyncException,), retry_backoff=True)
def google_workspace_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
