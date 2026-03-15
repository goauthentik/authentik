"""authentik saml source signal listener"""

from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest
from django.urls import reverse
from structlog.stdlib import get_logger

from authentik.core.models import USER_ATTRIBUTE_DELETE_ON_LOGOUT, AuthenticatedSession, User
from authentik.flows.challenge import PLAN_CONTEXT_ATTRS, PLAN_CONTEXT_TITLE, PLAN_CONTEXT_URL
from authentik.flows.models import in_memory_stage
from authentik.flows.stage import RedirectStage, SessionEndStage
from authentik.flows.views.executor import FlowExecutorView
from authentik.providers.saml.native_logout import NativeLogoutStageView
from authentik.sources.saml.models import SAMLSLOBindingTypes, SAMLSourceSession
from authentik.sources.saml.processors.logout_request import LogoutRequestProcessor
from authentik.sources.saml.views import AutosubmitStageView
from authentik.stages.user_logout.models import UserLogoutStage
from authentik.stages.user_logout.stage import flow_pre_user_logout

LOGGER = get_logger()

# Stages that redirect the user away from authentik. Source SLO stages must be
# inserted before these so they have a chance to execute.
TERMINAL_STAGE_VIEWS = {SessionEndStage, NativeLogoutStageView}


def _insert_before_terminal_stage(plan, stage):
    """Insert a stage before any terminal stage (SessionEndStage, NativeLogoutStageView)
    in the plan. Falls back to append if no terminal stage is found."""
    for i, binding in enumerate(plan.bindings):
        try:
            if binding.stage.view in TERMINAL_STAGE_VIEWS:
                plan.insert_stage(stage, index=i)
                return
        except NotImplementedError:
            continue
    plan.append_stage(stage)


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
            # Use the flow executor URL as relay_state so that after the IdP
            # processes the LogoutRequest and sends a LogoutResponse, the user
            # is redirected back to the flow to continue remaining stages.
            relay_state = request.build_absolute_uri(
                reverse(
                    "authentik_core:if-flow",
                    kwargs={"flow_slug": executor.flow.slug},
                )
            )

            processor = LogoutRequestProcessor(
                source=source,
                http_request=request,
                destination=source.slo_url,
                name_id=saml_session.name_id,
                name_id_format=saml_session.name_id_format,
                session_index=saml_session.session_index,
                relay_state=relay_state,
            )

            # Insert before terminal stages (SessionEndStage, NativeLogoutStageView)
            # so the SLO redirect runs before the flow ends or the user is
            # redirected away. Provider logout stages (at index 1/2) still run
            # first since they're inserted earlier.
            if source.slo_binding == SAMLSLOBindingTypes.REDIRECT:
                redirect_url = processor.get_redirect_url()
                stage = in_memory_stage(RedirectStage, destination=redirect_url)
            else:
                # POST binding
                form_data = processor.get_post_form_data()
                executor.plan.context[PLAN_CONTEXT_TITLE] = f"Logging out of {source.name}..."
                executor.plan.context[PLAN_CONTEXT_URL] = source.slo_url
                executor.plan.context[PLAN_CONTEXT_ATTRS] = form_data
                stage = in_memory_stage(AutosubmitStageView)

            _insert_before_terminal_stage(executor.plan, stage)

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
