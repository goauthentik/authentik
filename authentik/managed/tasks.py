"""managed tasks"""
from django.db import DatabaseError

from authentik.core.tasks import CELERY_APP
from authentik.events.monitored_tasks import PrefilledMonitoredTask, TaskResult, TaskResultStatus
from authentik.managed.manager import ObjectManager


@CELERY_APP.task(bind=True, base=PrefilledMonitoredTask)
def managed_reconcile(self: PrefilledMonitoredTask):
    """Run ObjectManager to ensure objects are up-to-date"""
    try:
        ObjectManager().run()
        self.set_status(
            TaskResult(TaskResultStatus.SUCCESSFUL, ["Successfully updated managed models."])
        )
    except DatabaseError as exc:  # pragma: no cover
        self.set_status(TaskResult(TaskResultStatus.WARNING, [str(exc)]))
