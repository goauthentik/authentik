"""authentik core tasks"""

from datetime import datetime, timedelta

from django.utils.timezone import now
from structlog.stdlib import get_logger

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    ExpiringModel,
    User,
)
from authentik.events.system_tasks import SystemTask, TaskStatus, prefill_task
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def clean_expired_models(self: SystemTask):
    """Remove expired objects"""
    messages = []
    for cls in ExpiringModel.__subclasses__():
        cls: ExpiringModel
        objects = (
            cls.objects.all().exclude(expiring=False).exclude(expiring=True, expires__gt=now())
        )
        amount = objects.count()
        for obj in objects:
            obj.expire_action()
        LOGGER.debug("Expired models", model=cls, amount=amount)
        messages.append(f"Expired {amount} {cls._meta.verbose_name_plural}")
    self.set_status(TaskStatus.SUCCESSFUL, *messages)


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def clean_temporary_users(self: SystemTask):
    """Remove temporary users created by SAML Sources"""
    _now = datetime.now()
    messages = []
    deleted_users = 0
    for user in User.objects.filter(**{f"attributes__{USER_ATTRIBUTE_GENERATED}": True}):
        if not user.attributes.get(USER_ATTRIBUTE_EXPIRES):
            continue
        delta: timedelta = _now - datetime.fromtimestamp(
            user.attributes.get(USER_ATTRIBUTE_EXPIRES)
        )
        if delta.total_seconds() > 0:
            LOGGER.debug("User is expired and will be deleted.", user=user, delta=delta)
            user.delete()
            deleted_users += 1
    messages.append(f"Successfully deleted {deleted_users} users.")
    self.set_status(TaskStatus.SUCCESSFUL, *messages)
