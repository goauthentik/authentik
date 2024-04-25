"""Google Provider tasks"""

from authentik.enterprise.providers.google.models import GoogleProvider
from authentik.events.system_tasks import SystemTask
from authentik.lib.sync.outgoing.tasks import SyncTasks
from authentik.root.celery import CELERY_APP

sync_tasks = SyncTasks(GoogleProvider)


@CELERY_APP.task()
def google_sync_objects(*args, **kwargs):
    return sync_tasks.sync_objects(*args, **kwargs)


@CELERY_APP.task(base=SystemTask, bind=True)
def google_sync(self, provider_pk: int, *args, **kwargs):
    return sync_tasks.sync_single(self, provider_pk, google_sync_objects)


@CELERY_APP.task()
def google_sync_all():
    return sync_tasks.sync_all(google_sync)


@CELERY_APP.task()
def google_sync_direct(*args, **kwargs):
    return sync_tasks.sync_signal_direct(*args, **kwargs)


@CELERY_APP.task()
def google_sync_m2m(*args, **kwargs):
    return sync_tasks.sync_signal_m2m(*args, **kwargs)
