from django.contrib.auth.signals import user_logged_out
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest

from authentik.core.models import AuthenticatedSession, User
from authentik.providers.oauth2.models import AccessToken, DeviceToken, RefreshToken


@receiver(user_logged_out)
def user_logged_out_oauth_tokens_removal(sender, request: HttpRequest, user: User, **_):
    """Revoke tokens upon user logout"""
    if not request.session or not request.session.session_key:
        return
    AccessToken.objects.filter(
        user=user,
        session__session__session_key=request.session.session_key,
    ).delete()


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_oauth_tokens_removal(sender, instance: AuthenticatedSession, **_):
    """Revoke tokens upon user logout"""
    AccessToken.objects.filter(
        user=instance.user,
        session__session__session_key=instance.session.session_key,
    ).delete()


@receiver(post_save, sender=User)
def user_deactivated(sender, instance: User, **_):
    """Remove user tokens when deactivated"""
    if instance.is_active:
        return
    AccessToken.objects.filter(user=instance).delete()
    RefreshToken.objects.filter(user=instance).delete()
    DeviceToken.objects.filter(user=instance).delete()
