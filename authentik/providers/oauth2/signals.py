from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.flows.models import in_memory_stage
from authentik.outposts.tasks import hash_session_key
from authentik.providers.iframe_logout import IframeLogoutStageView
from authentik.providers.oauth2.constants import PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS
from authentik.providers.oauth2.models import (
    AccessToken,
    DeviceToken,
    OAuth2LogoutMethod,
    RefreshToken,
)
from authentik.providers.oauth2.tasks import backchannel_logout_notification_dispatch
from authentik.stages.user_logout.models import UserLogoutStage
from authentik.stages.user_logout.stage import flow_pre_user_logout

LOGGER = get_logger()


@receiver(flow_pre_user_logout)
def handle_flow_pre_user_logout(sender, request, user, executor, **kwargs):
    """Handle SAML and OIDC frontchannel logout when user logs out via flow"""

    # Only proceed if this is actually a UserLogoutStage
    if not isinstance(executor.current_stage, UserLogoutStage):
        return

    if not user.is_authenticated:
        return

    auth_session = AuthenticatedSession.from_request(request, user)
    if not auth_session:
        return

    oidc_access_tokens = (
        AccessToken.objects.filter(
            user=user,
            session=auth_session,
            provider__logout_method=OAuth2LogoutMethod.FRONTCHANNEL,
        )
        .exclude(provider__logout_uri="")
        .select_related("provider")
    )

    if not oidc_access_tokens.exists():
        LOGGER.debug("No sessions requiring IFrame frontchannel logout")
        return

    oidc_sessions = []

    for token in oidc_access_tokens:
        # Parse the logout URI and add query parameters
        parsed_url = urlparse(token.provider.logout_uri)

        query_params = {}
        query_params["iss"] = token.provider.get_issuer(request)
        if auth_session.session:
            query_params["sid"] = hash_session_key(auth_session.session.session_key)

        # Combine existing query params with new ones
        if parsed_url.query:
            existing_params = parse_qs(parsed_url.query, keep_blank_values=True)
            for key, value in existing_params.items():
                if key not in query_params:
                    query_params[key] = value[0] if len(value) == 1 else value

        # Build the final URL with query parameters
        logout_url = urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                urlencode(query_params),
                parsed_url.fragment,
            )
        )

        logout_data = {
            "url": logout_url,
            "provider_name": token.provider.name,
            "binding": "redirect",
            "provider_type": "oidc",
        }
        oidc_sessions.append(logout_data)

    if oidc_sessions:
        executor.plan.context[PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS] = oidc_sessions

        # Stage already exists, don't reinject it
        if not any(
            binding.stage.view == IframeLogoutStageView for binding in executor.plan.bindings
        ):
            iframe_stage = in_memory_stage(IframeLogoutStageView)
            executor.plan.insert_stage(iframe_stage, index=1)

        LOGGER.debug("Oauth iframe sessions gathered")


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_oauth_backchannel_logout_and_tokens_removal(
    sender, instance: AuthenticatedSession, **_
):
    """Revoke tokens upon user logout"""
    LOGGER.debug("Sending back-channel logout notifications signal!", session=instance)

    access_tokens = AccessToken.objects.select_related("provider").filter(
        user=instance.user,
        session__session__session_key=instance.session.session_key,
    )

    # Only send backchannel logout notifications for providers that have
    # logout_uri configured and backchannel logout method set
    backchannel_tokens = [
        (
            token.provider_id,
            token.id_token.iss,
            token.id_token.sub,
            instance.session.session_key,
        )
        for token in access_tokens
        if token.provider.logout_uri
        and token.provider.logout_method == OAuth2LogoutMethod.BACKCHANNEL
    ]

    if backchannel_tokens:
        backchannel_logout_notification_dispatch.send(revocations=backchannel_tokens)

    access_tokens.delete()


@receiver(post_save, sender=User)
def user_deactivated(sender, instance: User, **_):
    """Remove user tokens when deactivated"""
    if instance.is_active:
        return
    AccessToken.objects.including_expired().filter(user=instance).delete()
    RefreshToken.objects.including_expired().filter(user=instance).delete()
    DeviceToken.objects.including_expired().filter(user=instance).delete()
