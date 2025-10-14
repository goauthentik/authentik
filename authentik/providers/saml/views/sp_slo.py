"""SP-initiated SAML Single Logout Views"""

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.core.models import Application, AuthenticatedSession
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlan, FlowPlanner
from authentik.flows.stage import SessionEndStage
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLProvider, SAMLSession
from authentik.providers.saml.processors.logout_request_parser import LogoutRequestParser
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_REQUEST,
    PLAN_CONTEXT_SAML_RELAY_STATE,
    REQUEST_KEY_RELAY_STATE,
    REQUEST_KEY_SAML_REQUEST,
    REQUEST_KEY_SAML_RESPONSE,
)

LOGGER = get_logger()


class SPInitiatedSLOView(PolicyAccessView):
    """Handle SP-initiated SAML Single Logout requests"""

    flow: Flow

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan_context = {}

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
                **self.plan_context,
            },
        )
        plan.append_stage(in_memory_stage(SessionEndStage))

        # Remove samlsession from database
        auth_session = AuthenticatedSession.from_request(self.request, self.request.user)
        if auth_session:
            SAMLSession.objects.filter(
                session=auth_session,
                user=self.request.user,
                provider=self.provider,
            ).delete()
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
        # If we receive a logoutResponse, this means we are using native redirect
        # IDP SLO, so we want to redirect to our next provider
        if REQUEST_KEY_SAML_RESPONSE in request.GET:
            relay_state = request.GET.get(REQUEST_KEY_RELAY_STATE, "")
            if relay_state:
                return redirect(relay_state)

            # No RelayState provided, try to get return URL from plan context
            if SESSION_KEY_PLAN in request.session:
                plan: FlowPlan = request.session[SESSION_KEY_PLAN]
                relay_state = plan.context.get(PLAN_CONTEXT_SAML_RELAY_STATE)
                if relay_state:
                    return redirect(relay_state)

            # No relay state and no plan context - redirect to root
            return redirect("authentik_core:root-redirect")

        # For SAML logout requests, use the parent dispatch with auth checks
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
            self.plan_context[PLAN_CONTEXT_SAML_LOGOUT_REQUEST] = logout_request
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
        # Check if this is a LogoutResponse before doing any authentication checks
        # If we receive a logoutResponse, this means we are using native redirect
        # IDP SLO, so we want to redirect to our next provider
        if REQUEST_KEY_SAML_RESPONSE in request.POST:
            relay_state = request.POST.get(REQUEST_KEY_RELAY_STATE, "")
            if relay_state:
                return redirect(relay_state)

            # No RelayState provided, try to get return URL from plan context
            if SESSION_KEY_PLAN in request.session:
                plan: FlowPlan = request.session[SESSION_KEY_PLAN]
                relay_state = plan.context.get(PLAN_CONTEXT_SAML_RELAY_STATE)
                if relay_state:
                    return redirect(relay_state)

            # No relay state and no plan context - redirect to root
            return redirect("authentik_core:root-redirect")

        # For SAML logout requests, use the parent dispatch with auth checks
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
            self.plan_context[PLAN_CONTEXT_SAML_LOGOUT_REQUEST] = logout_request
        except CannotHandleAssertion as exc:
            LOGGER.info(str(exc))
            return bad_request_message(self.request, str(exc))
        return None
