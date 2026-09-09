"""WS-Fed Provider signals"""

from urllib.parse import urlencode, urlparse, urlunparse

from django.dispatch import receiver
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.enterprise.providers.ws_federation.models import WSFederationProvider
from authentik.enterprise.providers.ws_federation.processors.constants import (
    WS_FED_ACTION_SIGN_OUT_CLEANUP,
    WS_FED_POST_KEY_ACTION,
)
from authentik.flows.models import in_memory_stage
from authentik.flows.views.executor import FlowExecutorView
from authentik.providers.iframe_logout import IframeLogoutStageView
from authentik.providers.saml.models import SAMLBindings, SAMLSession
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_SAML_RELAY_STATE,
)
from authentik.stages.user_logout.models import UserLogoutStage
from authentik.stages.user_logout.stage import flow_pre_user_logout

LOGGER = get_logger()


@receiver(flow_pre_user_logout)
def handle_ws_fed_iframe_pre_user_logout(
    sender, request: HttpRequest, user: User, executor: FlowExecutorView, **kwargs
):
    """Handle WS-Fed iframe logout when user logs out via flow"""

    # Only proceed if this is actually a UserLogoutStage
    if not isinstance(executor.current_stage, UserLogoutStage):
        return

    if not user.is_authenticated:
        return

    auth_session = AuthenticatedSession.from_request(request, user)
    if not auth_session:
        return

    wsfed_sessions = SAMLSession.objects.filter(
        session=auth_session,
        user=user,
        expires__gt=timezone.now(),
        expiring=True,
        # Only get WS-Federation provider sessions
        provider__wsfederationprovider__isnull=False,
    ).select_related("provider__wsfederationprovider")

    if not wsfed_sessions.exists():
        LOGGER.debug("No sessions requiring IFrame frontchannel logout")
        return

    saml_sessions = []

    relay_state = request.build_absolute_uri(
        reverse("authentik_core:if-flow", kwargs={"flow_slug": executor.flow.slug})
    )

    # Store return URL in plan context as fallback if SP doesn't echo relay_state
    executor.plan.context[PLAN_CONTEXT_SAML_RELAY_STATE] = relay_state

    for session in wsfed_sessions:
        provider: WSFederationProvider = session.provider.wsfederationprovider
        parts = urlparse(str(provider.acs_url))
        parts = parts._replace(
            query=urlencode({WS_FED_POST_KEY_ACTION: WS_FED_ACTION_SIGN_OUT_CLEANUP})
        )
        logout_data = {
            "url": urlunparse(parts),
            "provider_name": provider.name,
            "binding": SAMLBindings.REDIRECT,
        }

        saml_sessions.append(logout_data)

    if saml_sessions:
        executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = saml_sessions
        # Stage already exists, don't reinject it
        if not any(
            binding.stage.view == IframeLogoutStageView for binding in executor.plan.bindings
        ):
            iframe_stage = in_memory_stage(IframeLogoutStageView)
            executor.plan.insert_stage(iframe_stage, index=1)

        LOGGER.debug("WSFed iframe sessions gathered")
