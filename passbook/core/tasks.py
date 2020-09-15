"""passbook core tasks"""
from django.utils.timezone import now
from structlog import get_logger

from passbook.core.models import ExpiringModel
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def clean_expired_models():
    """Remove expired objects"""
    for cls in ExpiringModel.__subclasses__():
        cls: ExpiringModel
        amount, _ = (
            cls.objects.all()
            .exclude(expiring=False)
            .exclude(expiring=True, expires__gt=now())
            .delete()
        )
        LOGGER.debug("Deleted expired models", model=cls, amount=amount)
