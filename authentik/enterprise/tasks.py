"""Enterprise tasks"""

from authentik.enterprise.license import LicenseKey
from authentik.events.models import TaskStatus
from authentik.tasks.tasks import TaskData, task


@task(bind=True)
def enterprise_update_usage(self: TaskData):
    """Update enterprise license status"""
    LicenseKey.get_total().record_usage()
    self.set_status(TaskStatus.SUCCESSFUL)
