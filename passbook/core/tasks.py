"""passbook core tasks"""
from django.utils.timezone import now
from structlog import get_logger

from passbook.core.models import Token
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def clean_tokens():
    """Remove expired tokens"""
    amount, _ = Token.objects.filter(expires__lt=now(), expiring=True).delete()
    LOGGER.debug("Deleted expired tokens", amount=amount)
