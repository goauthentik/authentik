"""Proxy provider signals"""
from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import AuthenticatedSession, User
from authentik.providers.proxy.tasks import proxy_on_logout


@receiver(user_logged_out)
def logout_proxy_revoke_direct(sender: type[User], request: HttpRequest, **_):
    """Catch logout by direct logout and forward to proxy providers"""
    proxy_on_logout.delay(request.session.session_key)


@receiver(pre_delete, sender=AuthenticatedSession)
def logout_proxy_revoke(sender: type[AuthenticatedSession], instance: AuthenticatedSession, **_):
    """Catch logout by expiring sessions being deleted"""
    proxy_on_logout.delay(instance.session_key)
