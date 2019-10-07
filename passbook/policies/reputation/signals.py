"""passbook reputation request signals"""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from ipware import get_client_ip
from structlog import get_logger

from passbook.core.models import User
from passbook.policies.reputation.models import IPReputation, UserReputation

LOGGER = get_logger()


def get_remote_ip(request):
    """Small wrapper of get_client_ip to catch errors"""
    try:
        remote_ip, _ = get_client_ip(request)
        if remote_ip:
            return remote_ip
        if 'ip' in request:
            return request['ip']
    except (AttributeError, ValueError):
        pass
    return '255.255.255.255'

def update_score(request, username, amount):
    """Update score for IP and User"""
    remote_ip = get_remote_ip(request)
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
def handle_failed_login(sender, request, credentials, **kwargs):
    """Lower Score for failed loging attempts"""
    update_score(request, credentials.get('username'), -1)

@receiver(user_logged_in)
def handle_successful_login(sender, request, user, **kwargs):
    """Raise score for successful attempts"""
    update_score(request, user.username, 1)
