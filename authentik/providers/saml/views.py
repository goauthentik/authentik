"""authentik SAML IDP Views"""
from django.urls.base import reverse_lazy
from authentik.providers.saml.forms import SAMLProviderImportForm
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
from django.views.generic.edit import FormView
from structlog import get_logger

from authentik.core.models import Application, Provider
from authentik.events.models import Event, EventAction
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from authentik.flows.stage import StageView
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.metadata import MetadataProcessor
from authentik.providers.saml.processors.request_parser import (
    AuthNRequest,
    AuthNRequestParser,
)
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode, nice64
from authentik.stages.consent.stage import PLAN_CONTEXT_CONSENT_TEMPLATE

LOGGER = get_logger()
URL_VALIDATOR = URLValidator(schemes=("http", "https"))
REQUEST_KEY_SAML_REQUEST = "SAMLRequest"
REQUEST_KEY_SAML_SIGNATURE = "Signature"
REQUEST_KEY_SAML_SIG_ALG = "SigAlg"
REQUEST_KEY_SAML_RESPONSE = "SAMLResponse"
REQUEST_KEY_RELAY_STATE = "RelayState"

SESSION_KEY_AUTH_N_REQUEST = "authn_request"


class SAMLSSOView(PolicyAccessView):
    """ "SAML SSO Base View, which plans a flow and injects our final stage.
    Calls get/post handler."""

    def resolve_provider_application(self):
        self.application = get_object_or_404(
            Application, slug=self.kwargs["application_slug"]
        )
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )

    def check_saml_request(self) -> Optional[HttpRequest]:
        """Handler to verify the SAML Request. Must be implemented by a subclass"""
        raise NotImplementedError

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Verify the SAML Request, and if valid initiate the FlowPlanner for the application"""
        # Call the method handler, which checks the SAML
        # Request and returns a HTTP Response on error
        method_response = self.check_saml_request()
        if method_response:
            return method_response
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            request,
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_APPLICATION: self.application,
                PLAN_CONTEXT_CONSENT_TEMPLATE: "providers/saml/consent.html",
            },
        )
        plan.append(in_memory_stage(SAMLFlowFinalView))
        request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_flows:flow-executor-shell",
            request.GET,
            flow_slug=self.provider.authorization_flow.slug,
        )

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """GET and POST use the same handler, but we can't
        override .dispatch easily because PolicyAccessView's dispatch"""
        return self.get(request, application_slug)


class SAMLSSOBindingRedirectView(SAMLSSOView):
    """SAML Handler for SSO/Redirect bindings, which are sent via GET"""

    def check_saml_request(self) -> Optional[HttpRequest]:
        """Handle REDIRECT bindings"""
        if REQUEST_KEY_SAML_REQUEST not in self.request.GET:
            LOGGER.info("handle_saml_request: SAML payload missing")
            return bad_request_message(
                self.request, "The SAML request payload is missing."
            )

        try:
            auth_n_request = AuthNRequestParser(self.provider).parse_detached(
                self.request.GET[REQUEST_KEY_SAML_REQUEST],
                self.request.GET.get(REQUEST_KEY_RELAY_STATE),
                self.request.GET.get(REQUEST_KEY_SAML_SIGNATURE),
                self.request.GET.get(REQUEST_KEY_SAML_SIG_ALG),
            )
            self.request.session[SESSION_KEY_AUTH_N_REQUEST] = auth_n_request
        except CannotHandleAssertion as exc:
            LOGGER.info(exc)
            return bad_request_message(self.request, str(exc))
        return None


@method_decorator(csrf_exempt, name="dispatch")
class SAMLSSOBindingPOSTView(SAMLSSOView):
    """SAML Handler for SSO/POST bindings"""

    def check_saml_request(self) -> Optional[HttpRequest]:
        """Handle POST bindings"""
        if REQUEST_KEY_SAML_REQUEST not in self.request.POST:
            LOGGER.info("check_saml_request: SAML payload missing")
            return bad_request_message(
                self.request, "The SAML request payload is missing."
            )

        try:
            auth_n_request = AuthNRequestParser(self.provider).parse(
                self.request.POST[REQUEST_KEY_SAML_REQUEST],
                self.request.POST.get(REQUEST_KEY_RELAY_STATE),
            )
            self.request.session[SESSION_KEY_AUTH_N_REQUEST] = auth_n_request
        except CannotHandleAssertion as exc:
            LOGGER.info(exc)
            return bad_request_message(self.request, str(exc))
        return None


class SAMLSSOBindingInitView(SAMLSSOView):
    """SAML Handler for for IdP Initiated login flows"""

    def check_saml_request(self) -> Optional[HttpRequest]:
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
            form_attrs = {
                "ACSUrl": provider.acs_url,
                REQUEST_KEY_SAML_RESPONSE: nice64(response),
            }
            if auth_n_request.relay_state:
                form_attrs[REQUEST_KEY_RELAY_STATE] = auth_n_request.relay_state
            return render(
                self.request,
                "generic/autosubmit_form.html",
                {
                    "url": provider.acs_url,
                    "title": _("Redirecting to %(app)s..." % {"app": application.name}),
                    "attrs": form_attrs,
                },
            )
        if provider.sp_binding == SAMLBindings.REDIRECT:
            url_args = {
                REQUEST_KEY_SAML_RESPONSE: deflate_and_base64_encode(response),
            }
            if auth_n_request.relay_state:
                url_args[REQUEST_KEY_RELAY_STATE] = auth_n_request.relay_state
            querystring = urlencode(url_args)
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
            ] = f'attachment; filename="{provider.name}_authentik_meta.xml"'
            return response


class MetadataImportView(LoginRequiredMixin, FormView):
    """Import flow from JSON Export; only allowed for superusers
    as these flows can contain python code"""

    form_class = SAMLProviderImportForm
    template_name = "administration/flow/import.html"
    success_url = reverse_lazy("authentik_admin:flows")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: SAMLProviderImportForm) -> HttpResponse:
        importer = FlowImporter(form.cleaned_data["flow"].read().decode())
        successful = importer.apply()
        if not successful:
            messages.error(self.request, _("Failed to import flow."))
        else:
            messages.success(self.request, _("Successfully imported flow."))
        return super().form_valid(form)
