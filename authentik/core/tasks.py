"""authentik core tasks"""
from datetime import datetime
from io import StringIO
from os import environ

from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from dbbackup.db.exceptions import CommandConnectorError
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core import management
from django.core.cache import cache
from django.utils.timezone import now
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, ExpiringModel
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.lib.config import CONFIG
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task()
def clean_expired_models(self: MonitoredTask):
    """Remove expired objects"""
    messages = []
    for cls in ExpiringModel.__subclasses__():
        cls: ExpiringModel
        objects = (
            cls.objects.all().exclude(expiring=False).exclude(expiring=True, expires__gt=now())
        )
        for obj in objects:
            obj.expire_action()
        amount = objects.count()
        LOGGER.debug("Expired models", model=cls, amount=amount)
        messages.append(f"Expired {amount} {cls._meta.verbose_name_plural}")
    # Special case
    amount = 0
    for session in AuthenticatedSession.objects.all():
        cache_key = f"{KEY_PREFIX}{session.session_key}"
        value = cache.get(cache_key)
        if not value:
            session.delete()
            amount += 1
    LOGGER.debug("Expired sessions", model=AuthenticatedSession, amount=amount)
    messages.append(f"Expired {amount} {AuthenticatedSession._meta.verbose_name_plural}")
    self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL, messages))


def should_backup() -> bool:
    """Check if we should be doing backups"""
    if SERVICE_HOST_ENV_NAME in environ and not CONFIG.y("postgresql.s3_backup.bucket"):
        LOGGER.info("Running in k8s and s3 backups are not configured, skipping")
        return False
    if not CONFIG.y_bool("postgresql.backup.enabled"):
        return False
    if settings.DEBUG:
        return False
    return True


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task()
def backup_database(self: MonitoredTask):  # pragma: no cover
    """Database backup"""
    self.result_timeout_hours = 25
    if not should_backup():
        self.set_status(TaskResult(TaskResultStatus.UNKNOWN, ["Backups are not configured."]))
        return
    try:
        start = datetime.now()
        out = StringIO()
        management.call_command("dbbackup", quiet=True, stdout=out)
        self.set_status(
            TaskResult(
                TaskResultStatus.SUCCESSFUL,
                [
                    f"Successfully finished database backup {naturaltime(start)} {out.getvalue()}",
                ],
            )
        )
        LOGGER.info("Successfully backed up database.")
    except (
        IOError,
        BotoCoreError,
        ClientError,
        Boto3Error,
        PermissionError,
        CommandConnectorError,
        ValueError,
    ) as exc:
        self.set_status(TaskResult(TaskResultStatus.ERROR).with_error(exc))
