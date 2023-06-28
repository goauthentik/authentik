"""Run worker"""
from sys import exit as sysexit
from tempfile import tempdir

from celery.apps.worker import Worker
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


class Command(BaseCommand):
    """Run worker"""

    def handle(self, **options):
        close_old_connections()
        if CONFIG.y_bool("remote_debug"):
            import debugpy

            debugpy.listen(("0.0.0.0", 6900))  # nosec
        worker: Worker = CELERY_APP.Worker(
            no_color=False,
            quiet=True,
            optimization="fair",
            max_tasks_per_child=1,
            autoscale=(3, 1),
            task_events=True,
            beat=True,
            schedule_filename=f"{tempdir}/celerybeat-schedule",
            queues=["authentik", "authentik_scheduled", "authentik_events"],
        )
        for task in CELERY_APP.tasks:
            LOGGER.debug("Registered task", task=task)

        worker.start()
        sysexit(worker.exitcode)
