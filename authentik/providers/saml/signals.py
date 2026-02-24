"""SAML Provider signals"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.flows.models import in_memory_stage
from authentik.flows.views.executor import FlowExecutorView
from authentik.providers.iframe_logout import IframeLogoutStageView
from authentik.providers.saml.models import SAMLBindings, SAMLLogoutMethods, SAMLSession
from authentik.providers.saml.native_logout import NativeLogoutStageView
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.providers.saml.tasks import send_saml_logout_request
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS,
    PLAN_CONTEXT_SAML_RELAY_STATE,
)
from authentik.stages.user_logout.models import UserLogoutStage
from authentik.stages.user_logout.stage import flow_pre_user_logout

LOGGER = get_logger()


@receiver(flow_pre_user_logout)
def handle_saml_iframe_pre_user_logout(
    sender, request: HttpRequest, user: User, executor: FlowExecutorView, **kwargs
):
    """Handle SAML iframe logout when user logs out via flow"""

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
            provider__logout_method=SAMLLogoutMethods.FRONTCHANNEL_IFRAME,
        )
        .exclude(provider__sls_url="")
        .select_related("provider")
    )

    if not iframe_saml_sessions.exists():
        LOGGER.debug("No sessions requiring IFrame frontchannel logout")
        return

    saml_sessions = []

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

    if saml_sessions:
        executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS] = saml_sessions
        # Stage already exists, don't reinject it
        if not any(
            binding.stage.view == IframeLogoutStageView for binding in executor.plan.bindings
        ):
            iframe_stage = in_memory_stage(IframeLogoutStageView)
            executor.plan.insert_stage(iframe_stage, index=1)

        LOGGER.debug("saml iframe sessions gathered")


@receiver(flow_pre_user_logout)
def handle_flow_pre_user_logout(
    sender, request: HttpRequest, user: User, executor: FlowExecutorView, **kwargs
):
    """Handle SAML native logout when user logs out via logout flow"""

    # Only proceed if this is actually a UserLogoutStage
    if not isinstance(executor.current_stage, UserLogoutStage):
        return

    if not user.is_authenticated:
        return

    auth_session = AuthenticatedSession.from_request(request, user)
    if not auth_session:
        return

    native_saml_sessions = (
        SAMLSession.objects.filter(
            session=auth_session,
            user=user,
            expires__gt=timezone.now(),
            expiring=True,
            provider__logout_method=SAMLLogoutMethods.FRONTCHANNEL_NATIVE,
        )
        .exclude(provider__sls_url="")
        .select_related("provider")
    )

    if not native_saml_sessions.exists():
        return

    native_sessions = []

    # Generate return URL back to the flow using the interface URL
    relay_state = request.build_absolute_uri(
        reverse("authentik_core:if-flow", kwargs={"flow_slug": executor.flow.slug})
    )

    # Store return URL in plan context as fallback if SP doesn't echo relay_state
    executor.plan.context[PLAN_CONTEXT_SAML_RELAY_STATE] = relay_state

    for session in native_saml_sessions:
        try:
            processor = LogoutRequestProcessor(
                provider=session.provider,
                user=None,  # User is already logged out
                destination=session.provider.sls_url,
                name_id=session.name_id,
                name_id_format=session.name_id_format,
                session_index=session.session_index,
                relay_state=relay_state,
            )

            if session.provider.sls_binding == SAMLBindings.POST:
                form_data = processor.get_post_form_data()
                logout_data = {
                    "post_url": session.provider.sls_url,
                    "saml_request": form_data["SAMLRequest"],
                    "saml_relay_state": form_data["RelayState"],
                    "provider_name": session.provider.name,
                    "saml_binding": SAMLBindings.POST,
                }
            else:
                logout_url = processor.get_redirect_url()
                logout_data = {
                    "redirect_url": logout_url,
                    "provider_name": session.provider.name,
                    "saml_binding": SAMLBindings.REDIRECT,
                }

            native_sessions.append(logout_data)
        except (KeyError, AttributeError) as exc:
            LOGGER.warning(
                "Failed to generate SAML native logout data",
                provider=session.provider.name,
                exc=exc,
            )

    if native_sessions:
        executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_NATIVE_SESSIONS] = native_sessions
        native_logout_stage = in_memory_stage(NativeLogoutStageView)
        executor.plan.insert_stage(native_logout_stage, index=2)


@receiver(pre_delete, sender=AuthenticatedSession)
def user_session_deleted_saml_logout(sender, instance: AuthenticatedSession, **_):
    """Send SAML backchannel logout requests when user session is deleted"""

    backchannel_saml_sessions = (
        SAMLSession.objects.filter(
            session=instance,
            provider__logout_method=SAMLLogoutMethods.BACKCHANNEL,
            provider__sls_binding=SAMLBindings.POST,
        )
        .exclude(provider__sls_url="")
        .select_related("provider", "user")
    )

    for saml_session in backchannel_saml_sessions:
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
    """Send SAML backchannel logout requests when user is deactivated"""
    if instance.is_active:
        return

    backchannel_saml_sessions = (
        SAMLSession.objects.filter(
            user=instance,
            provider__logout_method=SAMLLogoutMethods.BACKCHANNEL,
            provider__sls_binding=SAMLBindings.POST,
        )
        .exclude(provider__sls_url="")
        .select_related("provider")
    )

    for saml_session in backchannel_saml_sessions:
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
