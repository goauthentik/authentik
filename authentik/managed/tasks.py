"""managed tasks"""
from django.db import DatabaseError

from authentik.core.tasks import CELERY_APP
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.managed.manager import ObjectManager


@CELERY_APP.task(
    bind=True,
    base=MonitoredTask,
    retry_backoff=True,
)
@prefill_task
def managed_reconcile(self: MonitoredTask):
    """Run ObjectManager to ensure objects are up-to-date"""
    try:
        ObjectManager().run()
        self.set_status(
            TaskResult(TaskResultStatus.SUCCESSFUL, ["Successfully updated managed models."])
        )
    except DatabaseError as exc:  # pragma: no cover
        self.set_status(TaskResult(TaskResultStatus.WARNING, [str(exc)]))
        self.retry()
