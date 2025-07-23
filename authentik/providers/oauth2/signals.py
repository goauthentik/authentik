from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.providers.oauth2.models import AccessToken, DeviceToken, RefreshToken
from authentik.providers.oauth2.tasks import send_backchannel_logout_notification

LOGGER = get_logger()


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_oauth_tokens_removal(sender, instance: AuthenticatedSession, **_):
    """Revoke tokens upon user logout"""
    AccessToken.objects.filter(
        user=instance.user,
        session__session__session_key=instance.session.session_key,
    ).delete()


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_backchannel_logout(sender, instance: AuthenticatedSession, **_):
    """Send back-channel logout notifications upon session deletion"""
    try:
        send_backchannel_logout_notification(session=instance)
    except Exception as exc:
        # Log the error but don't fail the session deletion process
        LOGGER.warning(
            "Failed to send back-channel logout notifications",
            user=instance.user.username,
            session_key=instance.session.session_key,
            error=str(exc),
        )


@receiver(post_save, sender=User)
def user_deactivated(sender, instance: User, **_):
    """Remove user tokens when deactivated"""
    if instance.is_active:
        return
    AccessToken.objects.filter(user=instance).delete()
    RefreshToken.objects.filter(user=instance).delete()
    DeviceToken.objects.filter(user=instance).delete()
