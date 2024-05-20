"""Enterprise tasks"""

from authentik.enterprise.license import LicenseKey
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask, prefill_task
from authentik.root.celery import CELERY_APP


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def enterprise_update_usage(self: SystemTask):
    """Update enterprise license status"""
    LicenseKey.get_total().record_usage()
    self.set_status(TaskStatus.SUCCESSFUL)
