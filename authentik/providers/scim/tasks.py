"""SCIM Provider tasks"""

from authentik.lib.sync.outgoing.tasks import (
    SyncAllTask,
    SyncObjectTask,
    SyncSignalDirectTask,
    SyncSignalM2MTask,
    SyncSingleTask,
)
from authentik.providers.scim.models import SCIMProvider
from authentik.root.celery import CELERY_APP

scim_sync_objects = CELERY_APP.register_task(SyncObjectTask(SCIMProvider))
scim_sync = CELERY_APP.register_task(SyncSingleTask(SCIMProvider, scim_sync_objects))
scim_sync_all = CELERY_APP.register_task(SyncAllTask(SCIMProvider, scim_sync))
scim_sync_direct = CELERY_APP.register_task(SyncSignalDirectTask(SCIMProvider))
scim_sync_m2m = CELERY_APP.register_task(SyncSignalM2MTask(SCIMProvider))
