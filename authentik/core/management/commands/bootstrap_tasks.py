"""Run bootstrap tasks"""
from django.core.management.base import BaseCommand

from authentik.root.celery import _get_startup_tasks


class Command(BaseCommand):  # pragma: no cover
    """Run bootstrap tasks to ensure certain objects are created"""

    def handle(self, **options):
        tasks = _get_startup_tasks()
        for task in tasks:
            task()
