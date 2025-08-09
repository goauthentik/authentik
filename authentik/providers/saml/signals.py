"""SAML Provider signals"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.providers.saml.models import SAMLSession
from authentik.providers.saml.tasks import send_saml_logout_request

LOGGER = get_logger()


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_saml_logout(sender, instance: AuthenticatedSession, **_):
    """Send SAML logout requests for providers that support backchannel logout
    via POST request when user session is deleted"""

    saml_sessions = SAMLSession.objects.filter(
        session=instance,
        provider__sls_url__isnull=False,
        provider__backchannel_post_logout=True,
        provider__sls_binding="post",
    ).select_related("provider", "user")

    for saml_session in saml_sessions:
        LOGGER.info(
            "Triggering backchannel SAML logout for deleted user session",
            user=saml_session.user,
            provider=saml_session.provider.name,
            session_index=saml_session.session_index,
        )

        send_saml_logout_request.send(
            provider_pk=saml_session.provider.pk,
            sls_url=saml_session.provider.sls_url,
            name_id=saml_session.name_id,
            name_id_format=saml_session.name_id_format,
            session_index=saml_session.session_index,
        )


@receiver(post_save, sender=User)
def user_deactivated_saml_logout(sender, instance: User, **kwargs):
    """Send SAML logout requests when user is deactivated"""

    saml_sessions = SAMLSession.objects.filter(
        user=instance,
        provider__sls_url__isnull=False,
        provider__backchannel_post_logout=True,
        provider__sls_binding="post",
    ).select_related("provider")

    for saml_session in saml_sessions:
        LOGGER.info(
            "Triggering backchannel SAML logout for deactivated user",
            user=instance,
            provider=saml_session.provider.name,
            session_index=saml_session.session_index,
        )

        send_saml_logout_request.send(
            provider_pk=saml_session.provider.pk,
            sls_url=saml_session.provider.sls_url,
            name_id=saml_session.name_id,
            name_id_format=saml_session.name_id_format,
            session_index=saml_session.session_index,
        )
