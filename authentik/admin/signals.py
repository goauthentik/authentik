"""admin signals"""

from django.dispatch import receiver

from authentik.admin.apps import GAUGE_WORKERS
from authentik.root.celery import CELERY_APP
from authentik.root.monitoring import monitoring_set


@receiver(monitoring_set)
def monitoring_set_workers(sender, **kwargs):
    """Set worker gauge"""
    count = len(CELERY_APP.control.ping(timeout=0.5))
    GAUGE_WORKERS.set(count)
