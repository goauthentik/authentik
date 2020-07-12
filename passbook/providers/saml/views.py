"""passbook SAML IDP Views"""
from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import URLValidator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.core.models import Application, Provider
from passbook.flows.models import in_memory_stage
from passbook.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from passbook.flows.stage import StageView
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.lib.views import bad_request_message
from passbook.policies.mixins import PolicyAccessMixin
from passbook.providers.saml.exceptions import CannotHandleAssertion
from passbook.providers.saml.models import SAMLBindings, SAMLProvider
from passbook.providers.saml.processors.assertion import AssertionProcessor
from passbook.providers.saml.processors.metadata import MetadataProcessor
from passbook.providers.saml.processors.request_parser import (
    AuthNRequest,
    AuthNRequestParser,
)
from passbook.providers.saml.utils.encoding import nice64
from passbook.stages.consent.stage import PLAN_CONTEXT_CONSENT_TEMPLATE

LOGGER = get_logger()
URL_VALIDATOR = URLValidator(schemes=("http", "https"))
REQUEST_KEY_SAML_REQUEST = "SAMLRequest"
REQUEST_KEY_SAML_SIGNATURE = "Signature"
REQUEST_KEY_SAML_SIG_ALG = "SigAlg"
REQUEST_KEY_SAML_RESPONSE = "SAMLResponse"
REQUEST_KEY_RELAY_STATE = "RelayState"

SESSION_KEY_AUTH_N_REQUEST = "authn_request"


class SAMLSSOView(LoginRequiredMixin, PolicyAccessMixin, View):
    """"SAML SSO Base View, which plans a flow and injects our final stage.
    Calls get/post handler."""

    application: Application
    provider: SAMLProvider

    def dispatch(
        self, request: HttpRequest, *args, application_slug: str, **kwargs
    ) -> HttpResponse:
        self.application = get_object_or_404(Application, slug=application_slug)
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self.user_has_access(self.application).passing:
            return self.handle_no_permission_authorized()
        # Call the method handler, which checks the SAML Request
        method_response = super().dispatch(request, *args, application_slug, **kwargs)
        if method_response:
            return method_response
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            self.request,
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_TEMPLATE: "providers/saml/consent.html",
            },
        )
        plan.append(in_memory_stage(SAMLFlowFinalView))
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=self.provider.authorization_flow.slug,
        )


class SAMLSSOBindingRedirectView(SAMLSSOView):
    """SAML Handler for SSO/Redirect bindings, which are sent via GET"""

    # pylint: disable=unused-argument
    def get(  # lgtm [py/similar-function]
        self, request: HttpRequest, application_slug: str
    ) -> Optional[HttpResponse]:
        """Handle REDIRECT bindings"""
        if REQUEST_KEY_SAML_REQUEST not in request.GET:
            LOGGER.info("handle_saml_request: SAML payload missing")
            return bad_request_message(
                self.request, "The SAML request payload is missing."
            )

        try:
            auth_n_request = AuthNRequestParser(self.provider).parse_detached(
                request.GET[REQUEST_KEY_SAML_REQUEST],
                request.GET.get(REQUEST_KEY_RELAY_STATE),
                request.GET.get(REQUEST_KEY_SAML_SIGNATURE),
                request.GET.get(REQUEST_KEY_SAML_SIG_ALG),
            )
            self.request.session[SESSION_KEY_AUTH_N_REQUEST] = auth_n_request
        except CannotHandleAssertion as exc:
            LOGGER.info(exc)
            return bad_request_message(self.request, str(exc))
        return None


@method_decorator(csrf_exempt, name="dispatch")
class SAMLSSOBindingPOSTView(SAMLSSOView):
    """SAML Handler for SSO/POST bindings"""

    # pylint: disable=unused-argument
    def post(
        self, request: HttpRequest, application_slug: str
    ) -> Optional[HttpResponse]:
        """Handle POST bindings"""
        if REQUEST_KEY_SAML_REQUEST not in request.POST:
            LOGGER.info("handle_saml_request: SAML payload missing")
            return bad_request_message(
                self.request, "The SAML request payload is missing."
            )

        try:
            auth_n_request = AuthNRequestParser(self.provider).parse(
                request.POST[REQUEST_KEY_SAML_REQUEST],
                request.POST.get(REQUEST_KEY_RELAY_STATE),
            )
            self.request.session[SESSION_KEY_AUTH_N_REQUEST] = auth_n_request
        except CannotHandleAssertion as exc:
            LOGGER.info(exc)
            return bad_request_message(self.request, str(exc))
        return None


class SAMLSSOBindingInitView(SAMLSSOView):
    """SAML Handler for for IdP Initiated login flows"""

    # pylint: disable=unused-argument
    def get(
        self, request: HttpRequest, application_slug: str
    ) -> Optional[HttpResponse]:
        """Create SAML Response from scratch"""
        LOGGER.debug(
            "handle_saml_no_request: No SAML Request, using IdP-initiated flow."
        )
        auth_n_request = AuthNRequestParser(self.provider).idp_initiated()
        self.request.session[SESSION_KEY_AUTH_N_REQUEST] = auth_n_request


# This View doesn't have a URL on purpose, as its called by the FlowExecutor
class SAMLFlowFinalView(StageView):
    """View used by FlowExecutor after all stages have passed. Logs the authorization,
    and redirects to the SP (if REDIRECT is configured) or shows and auto-submit for
    (if POST is configured)."""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        application: Application = self.executor.plan.context[PLAN_CONTEXT_APPLICATION]
        provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=application.provider_id
        )
        # Log Application Authorization
        Event.new(
            EventAction.AUTHORIZE_APPLICATION,
            authorized_application=application,
            flow=self.executor.plan.flow_pk,
        ).from_http(self.request)

        if SESSION_KEY_AUTH_N_REQUEST not in self.request.session:
            return self.executor.stage_invalid()

        auth_n_request: AuthNRequest = self.request.session.pop(
            SESSION_KEY_AUTH_N_REQUEST
        )
        response = AssertionProcessor(
            provider, request, auth_n_request
        ).build_response()

        if provider.sp_binding == SAMLBindings.POST:
            return render(
                self.request,
                "generic/autosubmit_form.html",
                {
                    "url": provider.acs_url,
                    "title": _("Redirecting to %(app)s..." % {"app": application.name}),
                    "attrs": {
                        "ACSUrl": provider.acs_url,
                        REQUEST_KEY_SAML_RESPONSE: nice64(response.encode()),
                        REQUEST_KEY_RELAY_STATE: auth_n_request.relay_state,
                    },
                },
            )
        if provider.sp_binding == SAMLBindings.REDIRECT:
            querystring = urlencode(
                {
                    REQUEST_KEY_SAML_RESPONSE: nice64(response.encode()),
                    REQUEST_KEY_RELAY_STATE: auth_n_request.relay_state,
                }
            )
            return redirect(f"{provider.acs_url}?{querystring}")
        return bad_request_message(request, "Invalid sp_binding specified")


class DescriptorDownloadView(View):
    """Replies with the XML Metadata IDSSODescriptor."""

    @staticmethod
    def get_metadata(request: HttpRequest, provider: SAMLProvider) -> str:
        """Return rendered XML Metadata"""
        return MetadataProcessor(provider, request).build_entity_descriptor()

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Replies with the XML Metadata IDSSODescriptor."""
        application = get_object_or_404(Application, slug=application_slug)
        provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=application.provider_id
        )
        try:
            metadata = DescriptorDownloadView.get_metadata(request, provider)
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return bad_request_message(
                request, "Provider is not assigned to an application."
            )
        else:
            response = HttpResponse(metadata, content_type="application/xml")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{provider.name}_passbook_meta.xml"'
            return response
