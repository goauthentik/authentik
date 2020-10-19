"""Database backup task"""
from datetime import datetime
from io import StringIO

from botocore.exceptions import BotoCoreError, ClientError
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core import management
from structlog import get_logger

from passbook.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=MonitoredTask)
def backup_database(self: MonitoredTask):  # pragma: no cover
    """Database backup"""
    try:
        start = datetime.now()
        out = StringIO()
        management.call_command("dbbackup", quiet=True, stdout=out)
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL,
                [
                    f"Successfully finished database backup {naturaltime(start)}",
                    out.getvalue(),
                ],
            )
        )
        LOGGER.info("Successfully backed up database.")
    except (IOError, BotoCoreError, ClientError) as exc:
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
