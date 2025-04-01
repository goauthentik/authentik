"""Google Provider tasks"""

from dramatiq.actor import actor

from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.lib.sync.outgoing.tasks import SyncTasks

sync_tasks = SyncTasks(GoogleWorkspaceProvider)


@actor
def google_workspace_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@actor
def google_workspace_sync(provider_pk: int, *args, **kwargs):
    """Run full sync for Google Workspace provider"""
    return sync_tasks.sync_single(provider_pk, google_workspace_sync_objects)


@actor
def google_workspace_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@actor
def google_workspace_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
