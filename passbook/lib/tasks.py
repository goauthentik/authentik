"""passbook misc tasks"""
from django.core import management
from structlog import get_logger

from passbook.root.celery import CELERY_APP

LOGGER = get_logger()

@CELERY_APP.task()
def backup_database():
    """Backup database"""
    management.call_command('dbbackup')
    LOGGER.info('Successfully backed up database.')
