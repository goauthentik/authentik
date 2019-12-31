"""passbook reputation request signals"""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from structlog import get_logger

from passbook.core.models import User
from passbook.lib.utils.http import get_client_ip
from passbook.policies.reputation.models import IPReputation, UserReputation

LOGGER = get_logger()


def update_score(request, username, amount):
    """Update score for IP and User"""
    remote_ip = get_client_ip(request) or "255.255.255.255."
    ip_score, _ = IPReputation.objects.update_or_create(ip=remote_ip)
    ip_score.score += amount
    ip_score.save()
    LOGGER.debug("Updated score", amount=amount, for_ip=remote_ip)
    user = User.objects.filter(username=username)
    if not user.exists():
        return
    user_score, _ = UserReputation.objects.update_or_create(user=user.first())
    user_score.score += amount
    user_score.save()
    LOGGER.debug("Updated score", amount=amount, for_user=username)


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
