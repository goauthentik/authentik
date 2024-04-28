"""Google Provider tasks"""

from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.events.system_tasks import SystemTask
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.root.celery import CELERY_APP

sync_tasks = SyncTasks(GoogleWorkspaceProvider)


@CELERY_APP.task()
def google_workspace_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@CELERY_APP.task(base=SystemTask, bind=True)
def google_workspace_sync(self, provider_pk: int, *args, **kwargs):
    return sync_tasks.sync_single(self, provider_pk, google_workspace_sync_objects)


@CELERY_APP.task()
def google_workspace_sync_all():
    return sync_tasks.sync_all(google_workspace_sync)


@CELERY_APP.task()
def google_workspace_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@CELERY_APP.task()
def google_workspace_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
