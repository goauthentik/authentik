"""Enterprise tasks"""
from authentik.enterprise.models import LicenseKey
from authentik.root.celery import CELERY_APP
from authentik.tenants.models import Tenant


@CELERY_APP.task()
def calculate_license():
    """Calculate licensing status"""
    for tenant in Tenant.models.all():
        LicenseKey.get_total(tenant).record_usage(tenant)
