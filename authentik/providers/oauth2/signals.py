from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.providers.oauth2.models import AccessToken, DeviceToken, RefreshToken
from authentik.providers.oauth2.tasks import backchannel_logout_notification_dispatch

LOGGER = get_logger()


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_oauth_backchannel_logout_and_tokens_removal(
    sender, instance: AuthenticatedSession, **_
):
    """Revoke tokens upon user logout"""
    LOGGER.debug("Sending back-channel logout notifications signal!", session=instance)

    access_tokens = AccessToken.objects.filter(
        user=instance.user,
        session__session__session_key=instance.session.session_key,
    )

    backchannel_logout_notification_dispatch.send(
        revocations=[
            (
                token.provider_id,
                token.id_token.iss,
                token.id_token.sub,
                instance.session.session_key,
            )
            for token in access_tokens
        ],
    )

    access_tokens.delete()


@receiver(post_save, sender=User)
def user_deactivated(sender, instance: User, **_):
    """Remove user tokens when deactivated"""
    if instance.is_active:
        return
    AccessToken.objects.filter(user=instance).delete()
    RefreshToken.objects.filter(user=instance).delete()
    DeviceToken.objects.filter(user=instance).delete()
