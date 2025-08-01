"""SP-initiated SAML Single Logout Views"""

import base64
import json

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlanner
from authentik.flows.stage import SessionEndStage
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLProvider, SAMLSession
from authentik.providers.saml.processors.logout_request_parser import LogoutRequestParser
from authentik.providers.saml.views.flows import (
    REQUEST_KEY_RELAY_STATE,
    REQUEST_KEY_SAML_REQUEST,
    REQUEST_KEY_SAML_RESPONSE,
    SESSION_KEY_LOGOUT_REQUEST,
)

LOGGER = get_logger()


class SPInitiatedSLOView(PolicyAccessView):
    """Handle SP-initiated SAML Single Logout requests"""

    flow: Flow

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["application_slug"])
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )
        self.flow = self.provider.invalidation_flow or self.request.brand.flow_invalidation
        if not self.flow:
            raise Http404

    def check_saml_request(self) -> HttpRequest | None:
        """Handler to verify the SAML Request. Must be implemented by a subclass"""
        raise NotImplementedError

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Verify the SAML Request, and if valid initiate the FlowPlanner for the application"""

        # Call the method handler, which checks the SAML
        # Request and returns a HTTP Response on error
        method_response = self.check_saml_request()
        if method_response:
            return method_response
        planner = FlowPlanner(self.flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            request,
            {
                PLAN_CONTEXT_APPLICATION: self.application,
            },
        )
        plan.append_stage(in_memory_stage(SessionEndStage))
        return plan.to_redirect(self.request, self.flow)

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """GET and POST use the same handler, but we can't
        override .dispatch easily because PolicyAccessView's dispatch"""
        return self.get(request, application_slug)


class SPInitiatedSLOBindingRedirectView(SPInitiatedSLOView):
    """SAML Handler for SP initiated SLO/Redirect bindings, which are sent via GET"""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Override dispatch to handle logout responses before authentication check"""
        # Check if this is a LogoutResponse before doing any authentication checks
        if REQUEST_KEY_SAML_RESPONSE in request.GET:
            relay_state = request.GET.get(REQUEST_KEY_RELAY_STATE, "")
            LOGGER.debug("SAML logout response received", relay_state=relay_state)
            if relay_state:
                # Try to decode the relay state first
                try:
                    json_data = base64.urlsafe_b64decode(relay_state.encode()).decode()
                    data = json.loads(json_data)
                    # If it's our encoded format, redirect to the return URL
                    if isinstance(data, dict) and "return_url" in data:
                        LOGGER.debug(
                            "Decoded relay state, redirecting", return_url=data["return_url"]
                        )
                        return redirect(data["return_url"])
                except Exception as exc:
                    # If decoding fails, treat it as a regular URL
                    LOGGER.debug("Failed to decode relay state", exc=exc)
                    pass
                return redirect(relay_state)
            return redirect("authentik_core:root-redirect")

        # For regular SAML logout requests, use the parent dispatch
        return super().dispatch(request, *args, **kwargs)

    def check_saml_request(self) -> HttpRequest | None:
        # Logout responses are now handled in dispatch()
        if REQUEST_KEY_SAML_REQUEST not in self.request.GET:
            LOGGER.info("check_saml_request: SAML payload missing")
            return bad_request_message(self.request, "The SAML request payload is missing.")

        try:
            logout_request = LogoutRequestParser(self.provider).parse_detached(
                self.request.GET[REQUEST_KEY_SAML_REQUEST],
                relay_state=self.request.GET.get(REQUEST_KEY_RELAY_STATE, None),
            )
            self.request.session[SESSION_KEY_LOGOUT_REQUEST] = logout_request

            LOGGER.info(
                "SP-initiated logout request received",
                provider=self.provider.name,
                issuer=logout_request.issuer,
                session_index=logout_request.session_index,
                has_session_index=bool(logout_request.session_index),
            )

            # Remove the SAML session if we have a session index
            if logout_request.session_index:
                try:
                    saml_session = SAMLSession.objects.get(
                        session_index=logout_request.session_index, provider=self.provider
                    )
                    LOGGER.info(
                        "Removing SAML session for SP-initiated logout",
                        session_index=logout_request.session_index,
                        provider=self.provider.name,
                        user=saml_session.user,
                    )
                    saml_session.delete()
                except SAMLSession.DoesNotExist:
                    LOGGER.warning(
                        "SAML session not found for logout",
                        session_index=logout_request.session_index,
                        provider=self.provider.name,
                    )
        except CannotHandleAssertion as exc:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                provider=self.provider,
                message=str(exc),
            ).save()
            LOGGER.info(str(exc))
            return bad_request_message(self.request, str(exc))
        return None


@method_decorator(xframe_options_sameorigin, name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class SPInitiatedSLOBindingPOSTView(SPInitiatedSLOView):
    """SAML Handler for SP-initiated SLO with POST binding"""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Override dispatch to handle logout requests and responses"""
        # First check if this is a LogoutResponse (from our initiated logout)
        if REQUEST_KEY_SAML_RESPONSE in request.POST:
            relay_state = request.POST.get(REQUEST_KEY_RELAY_STATE, "")
            LOGGER.debug("SAML logout response received (POST)", relay_state=relay_state)
            if relay_state:
                # Try to decode the relay state first
                try:
                    json_data = base64.urlsafe_b64decode(relay_state.encode()).decode()
                    data = json.loads(json_data)
                    # If it's our encoded format, redirect to the return URL
                    if isinstance(data, dict) and "return_url" in data:
                        LOGGER.debug(
                            "Decoded relay state, redirecting", return_url=data["return_url"]
                        )
                        return redirect(data["return_url"])
                except Exception as exc:
                    # If decoding fails, treat it as a regular URL
                    LOGGER.debug("Failed to decode relay state", exc=exc)
                    pass
                return redirect(relay_state)
            return redirect("authentik_core:root-redirect")

        # Check if this is a LogoutRequest (SP-initiated logout)
        # We need to handle this before authentication check since user might already be logged out
        if REQUEST_KEY_SAML_REQUEST in request.POST:
            LOGGER.debug("SAML logout request in POST, processing without auth check")
            # Skip the PolicyAccessView's dispatch which requires authentication
            # Instead, manually resolve provider and handle the request
            try:
                self.resolve_provider_application()
            except (Application.DoesNotExist, SAMLProvider.DoesNotExist, Http404) as exc:
                LOGGER.warning("Failed to resolve application for SP logout", exc=exc)
                return bad_request_message(request, "Invalid application")

            # Now handle the logout request
            return self.post(request, *args, **kwargs)

        # For other requests, use the parent dispatch
        return super().dispatch(request, *args, **kwargs)

    def check_saml_request(self) -> HttpRequest | None:
        payload = self.request.POST
        # Logout responses are now handled in dispatch()
        if REQUEST_KEY_SAML_REQUEST not in payload:
            LOGGER.info("check_saml_request: SAML payload missing")
            return bad_request_message(self.request, "The SAML request payload is missing.")

        try:
            logout_request = LogoutRequestParser(self.provider).parse(
                payload[REQUEST_KEY_SAML_REQUEST],
                relay_state=payload.get(REQUEST_KEY_RELAY_STATE, None),
            )
            self.request.session[SESSION_KEY_LOGOUT_REQUEST] = logout_request

            LOGGER.info(
                "SP-initiated logout request received (POST)",
                provider=self.provider.name,
                issuer=logout_request.issuer,
                session_index=logout_request.session_index,
                has_session_index=bool(logout_request.session_index),
            )

            # Remove the SAML session if we have a session index
            if logout_request.session_index:
                try:
                    saml_session = SAMLSession.objects.get(
                        session_index=logout_request.session_index, provider=self.provider
                    )
                    LOGGER.info(
                        "Removing SAML session for SP-initiated logout (POST)",
                        session_index=logout_request.session_index,
                        provider=self.provider.name,
                        user=saml_session.user,
                    )
                    saml_session.delete()
                except SAMLSession.DoesNotExist:
                    LOGGER.warning(
                        "SAML session not found for logout (POST)",
                        session_index=logout_request.session_index,
                        provider=self.provider.name,
                    )
        except CannotHandleAssertion as exc:
            LOGGER.info(str(exc))
            return bad_request_message(self.request, str(exc))
        return None
