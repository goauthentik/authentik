"""authentik reputation request signals"""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.dispatch import receiver
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.lib.config import CONFIG
from authentik.lib.utils.http import get_client_ip
from authentik.policies.reputation.models import CACHE_KEY_IP_PREFIX, CACHE_KEY_USER_PREFIX
from authentik.stages.identification.signals import identification_failed

LOGGER = get_logger()
CACHE_TIMEOUT = int(CONFIG.y("redis.cache_timeout_reputation"))


def update_score(request: HttpRequest, username: str, amount: int):
    """Update score for IP and User"""
    remote_ip = get_client_ip(request)

    try:
        # We only update the cache here, as its faster than writing to the DB
        cache.get_or_set(CACHE_KEY_IP_PREFIX + remote_ip, 0, CACHE_TIMEOUT)
        cache.incr(CACHE_KEY_IP_PREFIX + remote_ip, amount)

        cache.get_or_set(CACHE_KEY_USER_PREFIX + username, 0, CACHE_TIMEOUT)
        cache.incr(CACHE_KEY_USER_PREFIX + username, amount)
    except ValueError as exc:
        LOGGER.warning("failed to set reputation", exc=exc)

    LOGGER.debug("Updated score", amount=amount, for_user=username, for_ip=remote_ip)


@receiver(user_login_failed)
# pylint: disable=unused-argument
def handle_failed_login(sender, request, credentials, **_):
    """Lower Score for failed login attempts"""
    if "username" in credentials:
        update_score(request, credentials.get("username"), -1)


@receiver(identification_failed)
# pylint: disable=unused-argument
def handle_identification_failed(sender, request, uid_field: str, **_):
    """Lower Score for failed identification attempts"""
    update_score(request, uid_field, -1)


@receiver(user_logged_in)
# pylint: disable=unused-argument
def handle_successful_login(sender, request, user, **_):
    """Raise score for successful attempts"""
    update_score(request, user.username, 1)
