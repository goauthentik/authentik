"""authentik core tasks"""

from datetime import datetime, timedelta

from django.conf import ImproperlyConfigured
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.contrib.sessions.backends.db import SessionStore as DBSessionStore
from django.core.cache import cache
from django.utils.timezone import now
from structlog.stdlib import get_logger

from authentik.core.models import (
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    AuthenticatedSession,
    ExpiringModel,
    User,
)
from authentik.tasks.models import TaskStatus
from authentik.lib.config import CONFIG
from authentik.tasks.tasks import TaskData, task

LOGGER = get_logger()


@task(bind=True)
def clean_expired_models(self: TaskData):
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
    # Special case
    amount = 0

    for session in AuthenticatedSession.objects.all():
        match CONFIG.get("session_storage", "cache"):
            case "cache":
                cache_key = f"{KEY_PREFIX}{session.session_key}"
                value = None
                try:
                    value = cache.get(cache_key)

                except Exception as exc:
                    LOGGER.debug("Failed to get session from cache", exc=exc)
                if not value:
                    session.delete()
                    amount += 1
            case "db":
                if not (
                    DBSessionStore.get_model_class()
                    .objects.filter(session_key=session.session_key, expire_date__gt=now())
                    .exists()
                ):
                    session.delete()
                    amount += 1
            case _:
                # Should never happen, as we check for other values in authentik/root/settings.py
                raise ImproperlyConfigured(
                    "Invalid session_storage setting, allowed values are db and cache"
                )
    if CONFIG.get("session_storage", "cache") == "db":
        DBSessionStore.clear_expired()
    LOGGER.debug("Expired sessions", model=AuthenticatedSession, amount=amount)

    messages.append(f"Expired {amount} {AuthenticatedSession._meta.verbose_name_plural}")
    self.set_status(TaskStatus.SUCCESSFUL, *messages)


@task(bind=True)
def clean_temporary_users(self: TaskData):
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
