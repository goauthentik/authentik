"""Reputation tasks"""
from django.core.cache import cache
from structlog import get_logger

from passbook.core.models import User
from passbook.policies.reputation.models import IPReputation, UserReputation
from passbook.policies.reputation.signals import (
    CACHE_KEY_IP_PREFIX,
    CACHE_KEY_USER_PREFIX,
)
from passbook.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def save_ip_reputation():
    """Save currently cached reputation to database"""
    keys = cache.keys(CACHE_KEY_IP_PREFIX + "*")
    objects_to_update = []
    for key in keys:
        score = cache.get(key)
        remote_ip = key.replace(CACHE_KEY_IP_PREFIX, "")
        rep, _ = IPReputation.objects.get_or_create(ip=remote_ip)
        rep.score = score
        objects_to_update.append(rep)
    IPReputation.objects.bulk_update(objects_to_update, ["score"])


@CELERY_APP.task()
def save_user_reputation():
    """Save currently cached reputation to database"""
    keys = cache.keys(CACHE_KEY_USER_PREFIX + "*")
    objects_to_update = []
    for key in keys:
        score = cache.get(key)
        username = key.replace(CACHE_KEY_USER_PREFIX, "")
        users = User.objects.filter(username=username)
        if not users.exists():
            LOGGER.info("User in cache does not exist, ignoring", username=username)
            continue
        rep, _ = UserReputation.objects.get_or_create(user=users.first())
        rep.score = score
        objects_to_update.append(rep)
    UserReputation.objects.bulk_update(objects_to_update, ["score"])
