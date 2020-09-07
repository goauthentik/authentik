"""passbook core tasks"""
from structlog import get_logger

from passbook.core.models import ExpiringModel
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def clean_expired_models():
    """Remove expired objects"""
    for cls in ExpiringModel.__subclasses__():
        cls: ExpiringModel
        amount, _ = cls.filter_not_expired().delete()
        LOGGER.debug("Deleted expired models", model=cls, amount=amount)
