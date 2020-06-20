"""passbook SAML IDP Views"""
from typing import Optional

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.validators import URLValidator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from signxml.util import strip_pem_header
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
from passbook.lib.utils.template import render_to_string
from passbook.lib.utils.urls import redirect_with_qs
from passbook.lib.views import bad_request_message
from passbook.policies.engine import PolicyEngine
from passbook.providers.saml.exceptions import CannotHandleAssertion
from passbook.providers.saml.models import SAMLBindings, SAMLProvider
from passbook.providers.saml.processors.types import SAMLResponseParams

LOGGER = get_logger()
URL_VALIDATOR = URLValidator(schemes=("http", "https"))
SESSION_KEY_SAML_REQUEST = "SAMLRequest"
SESSION_KEY_SAML_RESPONSE = "SAMLResponse"
SESSION_KEY_RELAY_STATE = "RelayState"
SESSION_KEY_PARAMS = "SAMLParams"


class SAMLAccessMixin:
    """SAML base access mixin, checks access to an application based on its policies"""

    request: HttpRequest
    application: Application
    provider: SAMLProvider

    def _has_access(self) -> bool:
        """Check if user has access to application, add an error if not"""
        policy_engine = PolicyEngine(self.application, self.request.user, self.request)
        policy_engine.build()
        result = policy_engine.result
        LOGGER.debug(
            "SAMLFlowInit _has_access",
            user=self.request.user,
            app=self.application,
            result=result,
        )
        if not result.passing:
            for message in result.messages:
                messages.error(self.request, _(message))
        return result.passing


class SAMLSSOView(LoginRequiredMixin, SAMLAccessMixin, View):
    """"SAML SSO Base View, which plans a flow and injects our final stage.
    Calls get/post handler."""

    def dispatch(
        self, request: HttpRequest, *args, application_slug: str, **kwargs
    ) -> HttpResponse:
        self.application = get_object_or_404(Application, slug=application_slug)
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )
        if not self._has_access():
            raise PermissionDenied()
        # Call the method handler, which checks the SAML Request
        method_response = super().dispatch(request, *args, application_slug, **kwargs)
        if method_response:
            return method_response
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            self.request,
            {PLAN_CONTEXT_SSO: True, PLAN_CONTEXT_APPLICATION: self.application},
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
        # Store these values now, because Django's login cycle won't preserve them.
        if SESSION_KEY_SAML_REQUEST not in request.GET:
            LOGGER.info("handle_saml_request: SAML payload missing")
            return bad_request_message(
                self.request, "The SAML request payload is missing."
            )

        self.request.session[SESSION_KEY_SAML_REQUEST] = request.GET[
            SESSION_KEY_SAML_REQUEST
        ]
        self.request.session[SESSION_KEY_RELAY_STATE] = request.GET.get(
            SESSION_KEY_RELAY_STATE, ""
        )

        try:
            self.provider.processor.can_handle(self.request)
            params = self.provider.processor.generate_response()
            self.request.session[SESSION_KEY_PARAMS] = params
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
        # Store these values now, because Django's login cycle won't preserve them.
        if SESSION_KEY_SAML_REQUEST not in request.POST:
            LOGGER.info("handle_saml_request: SAML payload missing")
            return bad_request_message(
                self.request, "The SAML request payload is missing."
            )

        self.request.session[SESSION_KEY_SAML_REQUEST] = request.POST[
            SESSION_KEY_SAML_REQUEST
        ]
        self.request.session[SESSION_KEY_RELAY_STATE] = request.POST.get(
            SESSION_KEY_RELAY_STATE, ""
        )

        try:
            self.provider.processor.can_handle(self.request)
            params = self.provider.processor.generate_response()
            self.request.session[SESSION_KEY_PARAMS] = params
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
        """Create saml params from scratch"""
        LOGGER.debug(
            "handle_saml_no_request: No SAML Request, using IdP-initiated flow."
        )
        self.provider.processor.is_idp_initiated = True
        self.provider.processor.init_deep_link(self.request)
        params = self.provider.processor.generate_response()
        self.request.session[SESSION_KEY_PARAMS] = params


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
        self.request.session.pop(SESSION_KEY_SAML_REQUEST, None)
        self.request.session.pop(SESSION_KEY_SAML_RESPONSE, None)
        self.request.session.pop(SESSION_KEY_RELAY_STATE, None)
        if SESSION_KEY_PARAMS not in self.request.session:
            return self.executor.stage_invalid()
        response: SAMLResponseParams = self.request.session.pop(SESSION_KEY_PARAMS)

        if provider.sp_binding == SAMLBindings.POST:
            return render(
                self.request,
                "providers/saml/autosubmit_form.html",
                {
                    "url": response.acs_url,
                    "application": application,
                    "attrs": {
                        "ACSUrl": response.acs_url,
                        SESSION_KEY_SAML_RESPONSE: response.saml_response,
                        SESSION_KEY_RELAY_STATE: response.relay_state,
                    },
                },
            )
        if provider.sp_binding == SAMLBindings.REDIRECT:
            querystring = urlencode(
                {
                    SESSION_KEY_SAML_RESPONSE: response.saml_response,
                    SESSION_KEY_RELAY_STATE: response.relay_state,
                }
            )
            return redirect(f"{response.acs_url}?{querystring}")
        return bad_request_message(request, "Invalid sp_binding specified")


class DescriptorDownloadView(LoginRequiredMixin, SAMLAccessMixin, View):
    """Replies with the XML Metadata IDSSODescriptor."""

    @staticmethod
    def get_metadata(request: HttpRequest, provider: SAMLProvider) -> str:
        """Return rendered XML Metadata"""
        entity_id = provider.issuer
        saml_sso_binding_post = request.build_absolute_uri(
            reverse(
                "passbook_providers_saml:sso-post",
                kwargs={"application_slug": provider.application.slug},
            )
        )
        saml_sso_binding_redirect = request.build_absolute_uri(
            reverse(
                "passbook_providers_saml:sso-redirect",
                kwargs={"application_slug": provider.application.slug},
            )
        )
        subject_format = provider.processor.subject_format
        ctx = {
            "saml_sso_binding_post": saml_sso_binding_post,
            "saml_sso_binding_redirect": saml_sso_binding_redirect,
            "entity_id": entity_id,
            "subject_format": subject_format,
        }
        if provider.signing_kp:
            ctx["cert_public_key"] = strip_pem_header(
                provider.signing_kp.certificate_data.replace("\r", "")
            ).replace("\n", "")
        return render_to_string("providers/saml/xml/metadata.xml", ctx)

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Replies with the XML Metadata IDSSODescriptor."""
        self.application = get_object_or_404(Application, slug=application_slug)
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )
        if not self._has_access():
            raise PermissionDenied()
        try:
            metadata = DescriptorDownloadView.get_metadata(request, self.provider)
        except Provider.application.RelatedObjectDoesNotExist:  # pylint: disable=no-member
            return bad_request_message(
                request, "Provider is not assigned to an application."
            )
        else:
            response = HttpResponse(metadata, content_type="application/xml")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{self.provider.name}_passbook_meta.xml"'
            return response
