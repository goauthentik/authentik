"""Proxy provider signals"""

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from authentik.core.models import AuthenticatedSession
from authentik.providers.proxy.tasks import proxy_on_logout


@receiver(pre_delete, sender=AuthenticatedSession)
def logout_proxy_revoke(sender: type[AuthenticatedSession], instance: AuthenticatedSession, **_):
    """Catch logout by expiring sessions being deleted"""
    proxy_on_logout.send(instance.session.session_key)
