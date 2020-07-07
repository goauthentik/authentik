"""passbook reputation request signals"""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.dispatch import receiver
from django.http import HttpRequest
from structlog import get_logger

from passbook.lib.utils.http import get_client_ip
from passbook.policies.reputation.models import (
    CACHE_KEY_IP_PREFIX,
    CACHE_KEY_USER_PREFIX,
)

LOGGER = get_logger()


def update_score(request: HttpRequest, username: str, amount: int):
    """Update score for IP and User"""
    remote_ip = get_client_ip(request) or "255.255.255.255"

    # We only update the cache here, as its faster than writing to the DB
    cache.get_or_set(CACHE_KEY_IP_PREFIX + remote_ip, 0)
    cache.incr(CACHE_KEY_IP_PREFIX + remote_ip, amount)

    cache.get_or_set(CACHE_KEY_USER_PREFIX + username, 0)
    cache.incr(CACHE_KEY_USER_PREFIX + username, amount)

    LOGGER.debug("Updated score", amount=amount, for_user=username, for_ip=remote_ip)


@receiver(user_login_failed)
# pylint: disable=unused-argument
def handle_failed_login(sender, request, credentials, **_):
    """Lower Score for failed loging attempts"""
    update_score(request, credentials.get("username"), -1)


@receiver(user_logged_in)
# pylint: disable=unused-argument
def handle_successful_login(sender, request, user, **_):
    """Raise score for successful attempts"""
    update_score(request, user.username, 1)
