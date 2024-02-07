"""Enterprise tasks"""

from authentik.enterprise.models import LicenseKey
from authentik.events.system_tasks import SystemTask
from authentik.root.celery import CELERY_APP


@CELERY_APP.task(base=SystemTask)
def calculate_license():
    """Calculate licensing status"""
    LicenseKey.get_total().record_usage()
