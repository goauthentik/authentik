"""SLO Views"""
from typing import Optional

from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.events.models import Event, EventAction
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request_parser import LogoutRequestParser
from authentik.providers.saml.views.flows import (
    REQUEST_KEY_RELAY_STATE,
    REQUEST_KEY_SAML_REQUEST,
    SESSION_KEY_LOGOUT_REQUEST,
)

LOGGER = get_logger()


class SAMLSLOView(PolicyAccessView):
    """ "SAML SLO Base View, which plans a flow and injects our final stage.
    Calls get/post handler."""

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["application_slug"])
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )

    def check_saml_request(self) -> Optional[HttpRequest]:
        """Handler to verify the SAML Request. Must be implemented by a subclass"""
        raise NotImplementedError

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Verify the SAML Request, and if valid initiate the FlowPlanner for the application"""
        # Call the method handler, which checks the SAML
        # Request and returns a HTTP Response on error
        method_response = self.check_saml_request()
        if method_response:
            return method_response
        return redirect(
            "authentik_core:if-session-end",
            application_slug=self.kwargs["application_slug"],
        )

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """GET and POST use the same handler, but we can't
        override .dispatch easily because PolicyAccessView's dispatch"""
        return self.get(request, application_slug)


class SAMLSLOBindingRedirectView(SAMLSLOView):
    """SAML Handler for SLO/Redirect bindings, which are sent via GET"""

    def check_saml_request(self) -> Optional[HttpRequest]:
        if REQUEST_KEY_SAML_REQUEST not in self.request.GET:
            LOGGER.info("check_saml_request: SAML payload missing")
            return bad_request_message(self.request, "The SAML request payload is missing.")

        try:
            logout_request = LogoutRequestParser(self.provider).parse_detached(
                self.request.GET[REQUEST_KEY_SAML_REQUEST],
                relay_state=self.request.GET.get(REQUEST_KEY_RELAY_STATE, None),
            )
            self.request.session[SESSION_KEY_LOGOUT_REQUEST] = logout_request
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
class SAMLSLOBindingPOSTView(SAMLSLOView):
    """SAML Handler for SLO/POST bindings"""

    def check_saml_request(self) -> Optional[HttpRequest]:
        payload = self.request.POST
        if REQUEST_KEY_SAML_REQUEST not in payload:
            LOGGER.info("check_saml_request: SAML payload missing")
            return bad_request_message(self.request, "The SAML request payload is missing.")

        try:
            logout_request = LogoutRequestParser(self.provider).parse(
                payload[REQUEST_KEY_SAML_REQUEST],
                relay_state=payload.get(REQUEST_KEY_RELAY_STATE, None),
            )
            self.request.session[SESSION_KEY_LOGOUT_REQUEST] = logout_request
        except CannotHandleAssertion as exc:
            LOGGER.info(str(exc))
            return bad_request_message(self.request, str(exc))
        return None
