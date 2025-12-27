"""authentik core tasks"""

from datetime import datetime, timedelta
from hashlib import sha256

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_channels_postgres.models import GroupChannel, Message
from django_postgres_cache.tasks import clear_expired_cache
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    USER_ATTRIBUTE_TRANSIENT_TOKEN,
    ExpiringModel,
    User,
)
from authentik.lib.utils.db import chunked_queryset
from authentik.tasks.middleware import CurrentTask

LOGGER = get_logger()


@actor(description=_("Remove expired objects."))
def clean_expired_models():
    self = CurrentTask.get_task()
    for cls in ExpiringModel.__subclasses__():
        cls: ExpiringModel
        objects = (
            cls.objects.all().exclude(expiring=False).exclude(expiring=True, expires__gt=now())
        )
        amount = objects.count()
        for obj in chunked_queryset(objects):
            obj.expire_action()
        LOGGER.debug("Expired models", model=cls, amount=amount)
        self.info(f"Expired {amount} {cls._meta.verbose_name_plural}")
    clear_expired_cache()
    for cls in [Message, GroupChannel]:
        objects = cls.objects.all().filter(expires__lt=now())
        amount = objects.count()
        for obj in chunked_queryset(objects):
            obj.delete()
        LOGGER.debug("Expired models", model=cls, amount=amount)
        self.info(f"Expired {amount} {cls._meta.verbose_name_plural}")


@actor(description=_("Remove temporary users created by SAML Sources."))
def clean_temporary_users():
    self = CurrentTask.get_task()
    _now = datetime.now()
    deleted_users = 0
    for user in User.objects.filter(**{f"attributes__{USER_ATTRIBUTE_GENERATED}": True}):
        if not user.attributes.get(USER_ATTRIBUTE_EXPIRES):
            continue
        transient_token = user.attributes.get(USER_ATTRIBUTE_TRANSIENT_TOKEN)
        if transient_token and sha256(user.username.encode("utf-8")).hexdigest() != transient_token:
            user.attributes.pop(USER_ATTRIBUTE_TRANSIENT_TOKEN, None)
            user.attributes.pop(USER_ATTRIBUTE_EXPIRES, None)
            user.save()
            continue
        delta: timedelta = _now - datetime.fromtimestamp(
            user.attributes.get(USER_ATTRIBUTE_EXPIRES)
        )
        if delta.total_seconds() > 0:
            LOGGER.debug("User is expired and will be deleted.", user=user, delta=delta)
            user.delete()
            deleted_users += 1
        print(f"Delta {delta}")
    self.info(f"Successfully deleted {deleted_users} users.")
