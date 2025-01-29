from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import User
from authentik.providers.oauth2.models import AccessToken, DeviceToken, RefreshToken


@receiver(user_logged_out)
def user_logged_out_oauth_access_token(sender, request: HttpRequest, user: User, **_):
    """Revoke access tokens upon user logout"""
    if not request.session or not request.session.session_key:
        return
    AccessToken.objects.filter(user=user, session__session_key=request.session.session_key).delete()


@receiver(post_save, sender=User)
def user_deactivated(sender, instance: User, **_):
    """Remove user tokens when deactivated"""
    if instance.is_active:
        return
    RefreshToken.objects.filter(session__user=instance).delete()
    DeviceToken.objects.filter(session__user=instance).delete()
