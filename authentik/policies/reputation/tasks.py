"""Reputation tasks"""
from django.core.cache import cache
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.lib.tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.policies.reputation.models import IPReputation, UserReputation
from authentik.policies.reputation.signals import (
    CACHE_KEY_IP_PREFIX,
    CACHE_KEY_USER_PREFIX,
)
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=MonitoredTask)
def save_ip_reputation(self: MonitoredTask):
    """Save currently cached reputation to database"""
    objects_to_update = []
    for key, score in cache.get_many(cache.keys(CACHE_KEY_IP_PREFIX + "*")).items():
        remote_ip = key.replace(CACHE_KEY_IP_PREFIX, "")
        rep, _ = IPReputation.objects.get_or_create(ip=remote_ip)
        rep.score = score
        objects_to_update.append(rep)
    IPReputation.objects.bulk_update(objects_to_update, ["score"])
    self.set_status(
        TaskResult(TaskResultStatus.SUCCESSFUL, ["Successfully updated IP Reputation"])
    )


@CELERY_APP.task(bind=True, base=MonitoredTask)
def save_user_reputation(self: MonitoredTask):
    """Save currently cached reputation to database"""
    objects_to_update = []
    for key, score in cache.get_many(cache.keys(CACHE_KEY_USER_PREFIX + "*")).items():
        username = key.replace(CACHE_KEY_USER_PREFIX, "")
        users = User.objects.filter(username=username)
        if not users.exists():
            LOGGER.info("User in cache does not exist, ignoring", username=username)
            continue
        rep, _ = UserReputation.objects.get_or_create(user=users.first())
        rep.score = score
        objects_to_update.append(rep)
    UserReputation.objects.bulk_update(objects_to_update, ["score"])
    self.set_status(
        TaskResult(
            TaskResultStatus.SUCCESSFUL, ["Successfully updated User Reputation"]
        )
    )
