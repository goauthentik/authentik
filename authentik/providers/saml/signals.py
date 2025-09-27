"""SAML Provider signals"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.flows.models import in_memory_stage
from authentik.flows.signals import flow_pre_user_logout
from authentik.providers.oauth2.models import AccessToken
from authentik.providers.saml.models import LogoutMethods, SAMLSession
from authentik.providers.saml.tasks import send_saml_logout_request
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS,
)
from authentik.stages.user_logout.models import UserLogoutStage

LOGGER = get_logger()

# Add context key for OIDC iframe logout sessions
PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS = "oidc_logout_iframe_sessions"


@receiver(flow_pre_user_logout)
def handle_flow_pre_user_logout(sender, request, user, executor, **kwargs):
    """Handle SAML and OIDC logout when user logs out via flow"""

    # Only proceed if this is actually a UserLogoutStage
    if not isinstance(executor.current_stage, UserLogoutStage):
        return

    try:
        auth_session = AuthenticatedSession.from_request(request, user)
    except ValueError:
        LOGGER.debug("No authenticated session found for logout")
        return

    if not auth_session:
        return

    # Get all frontchannel SAML sessions that need logout
    all_saml_sessions = (
        SAMLSession.objects.filter(
            session=auth_session,
            user=user,
            expires__gt=timezone.now(),
            expiring=True,
            provider__sls_url__isnull=False,
        )
        .exclude(provider__logout_method=LogoutMethods.BACKCHANNEL)
        .select_related("provider")
    )

    # Get all OIDC sessions with frontchannel logout URIs
    oidc_access_tokens = (
        AccessToken.objects.filter(
            user=user, session=auth_session, provider__frontchannel_logout_uri__isnull=False
        )
        .exclude(provider__frontchannel_logout_uri="")
        .select_related("provider")
    )

    if not all_saml_sessions.exists() and not oidc_access_tokens.exists():
        LOGGER.debug("No sessions requiring frontchannel logout")
        return

    # Separate sessions by logout method
    iframe_sessions = []
    redirect_sessions = []
    oidc_sessions = []

    # Process SAML sessions
    for session in all_saml_sessions:
        session_data = {
            "provider_pk": str(session.provider.pk),
            "session_index": session.session_index,
            "name_id": session.name_id,
            "name_id_format": session.name_id_format,
        }

        if session.provider.logout_method == LogoutMethods.FRONTCHANNEL_REDIRECT:
            redirect_sessions.append(session_data)
        else:  # frontchannel_iframe is the default
            iframe_sessions.append(session_data)

    # Process OIDC sessions (always use iframe for OIDC frontchannel)
    for token in oidc_access_tokens:
        # Get the raw JWT for the id_token
        id_token_dict = token.id_token.to_dict()
        id_token_jwt = token.id_token.to_jwt(token.provider)

        session_data = {
            "provider_pk": str(token.provider.pk),
            "id_token": {
                **id_token_dict,
                "raw": id_token_jwt,  # Include the raw JWT for logout
            },
            "session_id": auth_session.session.session_key,
        }
        oidc_sessions.append(session_data)

    # Inject stages based on what methods are needed
    # We use separate context keys for each logout method
    stages_injected = []

    if redirect_sessions:
        # Store redirect sessions in context for the redirect stage
        executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS] = redirect_sessions

        from authentik.providers.saml.idp_logout import SAMLLogoutStageView

        redirect_stage = in_memory_stage(SAMLLogoutStageView)
        executor.plan.insert_stage(redirect_stage)
        stages_injected.append("redirect")

        LOGGER.debug(
            "Injected SAML redirect logout stage",
            user=user,
            session_count=len(redirect_sessions),
        )

    # Combine SAML iframe sessions and OIDC sessions (both use iframe method)
    if iframe_sessions or oidc_sessions:
        # Store both SAML and OIDC sessions in their respective contexts
        if iframe_sessions:
            executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = iframe_sessions
        if oidc_sessions:
            executor.plan.context[PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS] = oidc_sessions

        from authentik.providers.saml.idp_logout import IframeLogoutStageView

        iframe_stage = in_memory_stage(IframeLogoutStageView)
        executor.plan.insert_stage(iframe_stage)
        stages_injected.append("iframe")

        LOGGER.debug(
            "Injected iframe logout stage",
            user=user,
            saml_session_count=len(iframe_sessions),
            oidc_session_count=len(oidc_sessions),
        )

    LOGGER.debug(
        "Injected logout stages via signal",
        user=user,
        total_saml_sessions=len(all_saml_sessions),
        total_oidc_sessions=len(oidc_sessions),
        redirect_sessions=len(redirect_sessions),
        iframe_sessions=len(iframe_sessions),
        oidc_sessions=len(oidc_sessions),
        stages=stages_injected,
    )


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_saml_logout(sender, instance: AuthenticatedSession, **_):
    """Send SAML logout requests for providers that support backchannel logout
    via POST request when user session is deleted"""

    saml_sessions = SAMLSession.objects.filter(
        session=instance,
        provider__sls_url__isnull=False,
        provider__logout_method="backchannel",
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
    if instance.is_active:
        return

    saml_sessions = SAMLSession.objects.filter(
        user=instance,
        provider__sls_url__isnull=False,
        provider__logout_method="backchannel",
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
