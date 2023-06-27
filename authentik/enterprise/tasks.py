"""Enterprise tasks"""
from django.core.cache import cache

from authentik.enterprise.models import LicenseKey
from authentik.root.celery import CELERY_APP

CACHE_KEY_LICENSE_LAST_VALID = "goauthentik.io/enterprise/license_last_valid"


@CELERY_APP.task()
def calculate_license():
    """Calculate licensing status"""
    total = LicenseKey.get_total()
    cache.set(
        CACHE_KEY_LICENSE_LAST_VALID,
        total.last_valid_date(),
    )
