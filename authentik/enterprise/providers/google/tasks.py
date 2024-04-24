"""Google Provider tasks"""

from authentik.enterprise.providers.google.models import GoogleProvider
from authentik.lib.sync.outgoing.tasks import (
    SyncAllTask,
    SyncObjectTask,
    SyncSignalDirectTask,
    SyncSignalM2MTask,
    SyncSingleTask,
)
from authentik.root.celery import CELERY_APP

google_sync_objects = CELERY_APP.register_task(SyncObjectTask(GoogleProvider))
google_sync = CELERY_APP.register_task(SyncSingleTask(GoogleProvider, google_sync_objects))
google_sync_all = CELERY_APP.register_task(SyncAllTask(GoogleProvider, google_sync))
google_sync_direct = CELERY_APP.register_task(SyncSignalDirectTask(GoogleProvider))
google_sync_m2m = CELERY_APP.register_task(SyncSignalM2MTask(GoogleProvider))
