"""passbook Worker management command"""

from logging import getLogger

from django.core.management.base import BaseCommand

from passbook.core.celery import CELERY_APP

LOGGER = getLogger(__name__)


class Command(BaseCommand):
    """Run Celery Worker"""

    def handle(self, *args, **options):
        """celery worker"""
        CELERY_APP.worker_main(['worker', '--autoscale=10,3', '-E', '-B'])
