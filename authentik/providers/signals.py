"""Shared Provider signals"""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession
from authentik.flows.models import in_memory_stage
from authentik.flows.signals import flow_pre_user_logout
from authentik.providers.logout import IframeLogoutStageView
from authentik.providers.oauth2.constants import PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS
from authentik.providers.oauth2.id_token import hash_session_key
from authentik.providers.oauth2.models import AccessToken, OAuth2LogoutMethod
from authentik.providers.saml.models import LogoutMethods, SAMLBindings, SAMLSession
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_SAML_RELAY_STATE,
)
from authentik.stages.user_logout.models import UserLogoutStage

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

    iframe_saml_sessions = (
        SAMLSession.objects.filter(
            session=auth_session,
            user=user,
            expires__gt=timezone.now(),
            expiring=True,
            provider__sls_url__isnull=False,
            provider__logout_method=LogoutMethods.FRONTCHANNEL_IFRAME,
        )
        .exclude(provider__sls_url="")
        .select_related("provider")
    )

    oidc_access_tokens = (
        AccessToken.objects.filter(
            user=user,
            session=auth_session,
            provider__logout_method=OAuth2LogoutMethod.FRONTCHANNEL,
            provider__logout_uri__isnull=False,
        )
        .exclude(provider__logout_uri="")
        .select_related("provider")
    )

    if not iframe_saml_sessions.exists() and not oidc_access_tokens.exists():
        LOGGER.debug("No sessions requiring IFrame frontchannel logout")
        return

    saml_sessions = []
    oidc_sessions = []

    relay_state = request.build_absolute_uri(
        reverse("authentik_core:if-flow", kwargs={"flow_slug": executor.flow.slug})
    )

    # Store return URL in plan context as fallback if SP doesn't echo relay_state
    executor.plan.context[PLAN_CONTEXT_SAML_RELAY_STATE] = relay_state

    for session in iframe_saml_sessions:
        try:
            processor = LogoutRequestProcessor(
                provider=session.provider,
                user=None,  # User context not needed for logout URL generation
                destination=session.provider.sls_url,
                name_id=session.name_id,
                name_id_format=session.name_id_format,
                session_index=session.session_index,
                relay_state=relay_state,
            )

            if session.provider.sls_binding == SAMLBindings.POST:
                form_data = processor.get_post_form_data()
                logout_data = {
                    "url": session.provider.sls_url,
                    "saml_request": form_data["SAMLRequest"],
                    "provider_name": session.provider.name,
                    "binding": SAMLBindings.POST,
                }
            else:
                logout_url = processor.get_redirect_url()
                logout_data = {
                    "url": logout_url,
                    "provider_name": session.provider.name,
                    "binding": SAMLBindings.REDIRECT,
                }

            saml_sessions.append(logout_data)
        except (KeyError, AttributeError) as exc:
            LOGGER.warning(
                "Failed to generate SAML logout URL",
                provider=session.provider.name,
                exc=exc,
            )

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
            "binding": SAMLBindings.REDIRECT,
            "provider_type": "oidc",
        }
        oidc_sessions.append(logout_data)

    if saml_sessions or oidc_sessions:
        if saml_sessions:
            executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = saml_sessions
        if oidc_sessions:
            executor.plan.context[PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS] = oidc_sessions

        iframe_stage = in_memory_stage(IframeLogoutStageView)
        executor.plan.insert_stage(iframe_stage, index=1)

    LOGGER.debug(
        "Injected logout stages via signal",
        user=user,
        total_saml_sessions=len(iframe_saml_sessions),
        total_oidc_sessions=len(oidc_sessions),
        saml_sessions=len(saml_sessions),
        oidc_sessions=len(oidc_sessions),
    )
