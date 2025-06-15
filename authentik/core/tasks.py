"""authentik core tasks"""

from datetime import datetime, timedelta

from django.utils.timezone import now
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    ExpiringModel,
    User,
)
from authentik.tasks.middleware import CurrentTask

LOGGER = get_logger()


@actor
def clean_expired_models():
    """Remove expired objects"""
    self = CurrentTask.get_task()
    for cls in ExpiringModel.__subclasses__():
        cls: ExpiringModel
        objects = (
            cls.objects.all().exclude(expiring=False).exclude(expiring=True, expires__gt=now())
        )
        amount = objects.count()
        for obj in objects:
            obj.expire_action()
        LOGGER.debug("Expired models", model=cls, amount=amount)
        self.info(f"Expired {amount} {cls._meta.verbose_name_plural}")


@actor
def clean_temporary_users():
    """Remove temporary users created by SAML Sources"""
    self = CurrentTask.get_task()
    _now = datetime.now()
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
    self.info(f"Successfully deleted {deleted_users} users.")
