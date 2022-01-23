"""authentik core tasks"""
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import cache
from django.utils.timezone import now
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, ExpiringModel
from authentik.events.monitored_tasks import (
    MonitoredTask,
    TaskResult,
    TaskResultStatus,
    prefill_task,
)
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=MonitoredTask)
@prefill_task
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

