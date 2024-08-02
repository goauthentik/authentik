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
    UserPasswordHistory,
)
from authentik.events.system_tasks import SystemTask, TaskStatus, prefill_task
from authentik.lib.config import CONFIG
from authentik.policies.models import PolicyBinding
from authentik.policies.unique_password.models import UniquePasswordPolicy
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
    LOGGER.debug("Expired sessions", model=AuthenticatedSession, amount=amount)

    messages.append(f"Expired {amount} {AuthenticatedSession._meta.verbose_name_plural}")
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


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def purge_password_history_table(self: SystemTask):
    """Remove all entries from the core.models.UserPasswordHistory table"""
    messages = []
    try:
        # n.b. a performance optimization to execute TRUNCATE
        # instead of all().delete() would eliminate any FK checks.
        UserPasswordHistory.objects.all().delete()
    except Exception as err:
        LOGGER.debug("Failed to purge core.models.UserPasswordHistory table.")
        self.set_error(err)
        return
    messages.append("Successfully purged core.models.UserPasswordHistory")
    self.set_status(TaskStatus.SUCCESSFUL, *messages)


@CELERY_APP.task()
def trim_user_password_history(user_pk: int):
    """Removes rows from core.models.UserPasswordHistory older than
    the `n` most recent entries.

    The `n` is defined by the largest configured value for all bound
    UniquePasswordPolicy policies.
    """
    unique_password_policies = UniquePasswordPolicy.objects.all()

    # All enable policy bindings for UniquePasswordPolicy
    enabled_bindings = PolicyBinding.objects.filter(policy__in=unique_password_policies).filter(
        enabled=True
    )

    if not enabled_bindings.exists():
        return

    num_rows_to_preserve = 0
    for binding in enabled_bindings:
        if hasattr(binding.policy, "num_historical_passwords"):
            num_rows_to_preserve = max(
                num_rows_to_preserve, binding.policy.num_historical_passwords
            )

    preservable_row_ids = (
        UserPasswordHistory.objects.filter(user__pk=user_pk)
        .order_by("-created_at")[:num_rows_to_preserve]
        .values_list("id", flat=True)
    )
    num_deleted, _ = UserPasswordHistory.objects.exclude(pk__in=list(preservable_row_ids)).delete()
    LOGGER.debug(
        "Deleted stale password history records for user", user_id=user_pk, records=num_deleted
    )
