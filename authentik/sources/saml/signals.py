"""authentik saml source signal listener"""

from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.models import USER_ATTRIBUTE_DELETE_ON_LOGOUT, AuthenticatedSession, User
from authentik.flows.challenge import PLAN_CONTEXT_ATTRS, PLAN_CONTEXT_TITLE, PLAN_CONTEXT_URL
from authentik.flows.models import in_memory_stage
from authentik.flows.stage import RedirectStage
from authentik.flows.views.executor import FlowExecutorView
from authentik.sources.saml.models import SAMLSLOBindingTypes, SAMLSourceSession
from authentik.sources.saml.processors.logout_request import LogoutRequestProcessor
from authentik.sources.saml.views import AutosubmitStageView
from authentik.stages.user_logout.models import UserLogoutStage
from authentik.stages.user_logout.stage import flow_pre_user_logout

LOGGER = get_logger()


@receiver(user_logged_out)
def on_user_logged_out(sender, request: HttpRequest, user: User, **_):
    """Delete temporary user if the `delete_on_logout` flag is enabled"""
    if not user:
        return
    if user.attributes.get(USER_ATTRIBUTE_DELETE_ON_LOGOUT, False):
        LOGGER.debug("Deleted temporary user", user=user)
        user.delete()


@receiver(flow_pre_user_logout)
def handle_saml_source_pre_user_logout(
    sender, request: HttpRequest, user: User, executor: FlowExecutorView, **kwargs
):
    """Handle SAML source SP-initiated SLO when user logs out via flow.
    Injects a stage into the logout flow to redirect the user to the IdP's SLO URL."""
    if not isinstance(executor.current_stage, UserLogoutStage):
        return

    if not user.is_authenticated:
        return

    auth_session = AuthenticatedSession.from_request(request, user)
    if not auth_session:
        return

    # Find SAMLSourceSessions for this user's current session
    saml_source_sessions = SAMLSourceSession.objects.filter(
        session=auth_session,
        user=user,
    ).select_related("source")

    for saml_session in saml_source_sessions:
        source = saml_session.source
        if not source.slo_url or not source.enabled:
            continue

        try:
            relay_state = request.build_absolute_uri("/")

            processor = LogoutRequestProcessor(
                source=source,
                http_request=request,
                destination=source.slo_url,
                name_id=saml_session.name_id,
                name_id_format=saml_session.name_id_format,
                session_index=saml_session.session_index,
                relay_state=relay_state,
            )

            if source.slo_binding == SAMLSLOBindingTypes.REDIRECT:
                redirect_url = processor.get_redirect_url()
                redirect_stage = in_memory_stage(RedirectStage, destination=redirect_url)
                executor.plan.insert_stage(redirect_stage, index=1)
            else:
                # POST binding
                form_data = processor.get_post_form_data()
                executor.plan.context[PLAN_CONTEXT_TITLE] = f"Logging out of {source.name}..."
                executor.plan.context[PLAN_CONTEXT_URL] = source.slo_url
                executor.plan.context[PLAN_CONTEXT_ATTRS] = form_data

                autosubmit_stage = in_memory_stage(AutosubmitStageView)
                executor.plan.insert_stage(autosubmit_stage, index=1)

            LOGGER.debug(
                "Injected SAML source SLO into logout flow",
                source=source.name,
                binding=source.slo_binding,
            )

        except (KeyError, AttributeError) as exc:
            LOGGER.warning(
                "Failed to generate SAML source logout request",
                source=source.name,
                exc=exc,
            )

    # Clean up SAMLSourceSessions for this auth session
    saml_source_sessions.delete()
