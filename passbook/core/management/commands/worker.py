"""passbook Worker management command"""

from logging import getLogger

from django.core.management.base import BaseCommand
from django.utils import autoreload

from passbook.root.celery import CELERY_APP

LOGGER = getLogger(__name__)


class Command(BaseCommand):
    """Run Celery Worker"""

    def handle(self, *args, **options):
        """celery worker"""
        autoreload.run_with_reloader(self.celery_worker)

    def celery_worker(self):
        """Run celery worker within autoreload"""
        autoreload.raise_last_exception()
        CELERY_APP.worker_main(['worker', '--autoscale=10,3', '-E', '-B'])
