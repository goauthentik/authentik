"""passbook core tasks"""
from django.utils.timezone import now
from structlog import get_logger

from passbook.core.models import ExpiringModel
from passbook.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=MonitoredTask)
def clean_expired_models(self: MonitoredTask):
    """Remove expired objects"""
    messages = []
    for cls in ExpiringModel.__subclasses__():
        cls: ExpiringModel
        amount, _ = (
            cls.objects.all()
            .exclude(expiring=False)
            .exclude(expiring=True, expires__gt=now())
            .delete()
        )
        LOGGER.debug("Deleted expired models", model=cls, amount=amount)
        messages.append(f"Deleted {amount} expired {cls._meta.verbose_name_plural}")
    self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL, messages))
