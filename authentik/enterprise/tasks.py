"""Enterprise tasks"""
from authentik.enterprise.models import LicenseKey
from authentik.root.celery import CELERY_APP


@CELERY_APP.task()
def calculate_license():
    """Calculate licensing status"""
    total = LicenseKey.get_total()
    total.record_usage()
