"""passbook core tasks"""
from datetime import datetime

from structlog import get_logger

from passbook.core.models import Nonce
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()

@CELERY_APP.task()
def clean_nonces():
    """Remove expired nonces"""
    amount, _ = Nonce.objects.filter(expires__lt=datetime.now(), expiring=True).delete()
    LOGGER.debug("Deleted expired nonces", amount=amount)
