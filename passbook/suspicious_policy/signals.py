"""passbook suspicious request signals"""
from logging import getLogger

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from ipware import get_client_ip

from passbook.core.models import User
from passbook.suspicious_policy.models import IPScore, UserScore

LOGGER = getLogger(__name__)


def update_score(request, username, amount):
    """Update score for IP and User"""
    remote_ip, _ = get_client_ip(request)
    if not remote_ip:
        remote_ip = '255.255.255.255'
    ip_score, _ = IPScore.objects.update_or_create(ip=remote_ip)
    ip_score.score += amount
    ip_score.save()
    LOGGER.debug("Added %s to score of IP %s", amount, remote_ip)
    user = User.objects.filter(username=username)
    if not user.exists():
        return
    user_score, _ = UserScore.objects.update_or_create(user=user.first())
    user_score.score += amount
    user_score.save()
    LOGGER.debug("Added %s to score of User %s", amount, username)

@receiver(user_login_failed)
def handle_failed_login(sender, request, credentials, **kwargs):
    """Lower Score for failed loging attempts"""
    update_score(request, credentials.get('username'), -1)

@receiver(user_logged_in)
def handle_successful_login(sender, request, user, **kwargs):
    """Raise score for successful attempts"""
    update_score(request, user.username, 1)
