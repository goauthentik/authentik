"""authentik reputation request signals"""
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from django.dispatch import receiver
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.signals import login_failed
from authentik.lib.config import CONFIG
from authentik.lib.utils.http import get_client_ip
from authentik.policies.reputation.models import CACHE_KEY_PREFIX
from authentik.policies.reputation.tasks import save_reputation
from authentik.stages.identification.signals import identification_failed

LOGGER = get_logger()
CACHE_TIMEOUT = CONFIG.get_int("redis.cache_timeout_reputation")


def update_score(request: HttpRequest, identifier: str, amount: int):
    """Update score for IP and User"""
    remote_ip = get_client_ip(request)

    try:
        # We only update the cache here, as its faster than writing to the DB
        score = cache.get_or_set(
            CACHE_KEY_PREFIX + remote_ip + "/" + identifier,
            {"ip": remote_ip, "identifier": identifier, "score": 0},
            CACHE_TIMEOUT,
        )
        score["score"] += amount
        cache.set(CACHE_KEY_PREFIX + remote_ip + "/" + identifier, score)
    except ValueError as exc:
        LOGGER.warning("failed to set reputation", exc=exc)

    LOGGER.debug("Updated score", amount=amount, for_user=identifier, for_ip=remote_ip)
    save_reputation.delay()


@receiver(login_failed)
def handle_failed_login(sender, request, credentials, **_):
    """Lower Score for failed login attempts"""
    if "username" in credentials:
        update_score(request, credentials.get("username"), -1)


@receiver(identification_failed)
def handle_identification_failed(sender, request, uid_field: str, **_):
    """Lower Score for failed identification attempts"""
    update_score(request, uid_field, -1)


@receiver(user_logged_in)
def handle_successful_login(sender, request, user, **_):
    """Raise score for successful attempts"""
    update_score(request, user.username, 1)
