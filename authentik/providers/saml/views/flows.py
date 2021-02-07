"""authentik SAML IDP Views"""
from django.core.validators import URLValidator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.flows.stage import StageView
from authentik.lib.views import bad_request_message
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.assertion import AssertionProcessor
from authentik.providers.saml.processors.request_parser import AuthNRequest
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode, nice64

LOGGER = get_logger()
URL_VALIDATOR = URLValidator(schemes=("http", "https"))
REQUEST_KEY_SAML_REQUEST = "SAMLRequest"
REQUEST_KEY_SAML_SIGNATURE = "Signature"
REQUEST_KEY_SAML_SIG_ALG = "SigAlg"
REQUEST_KEY_SAML_RESPONSE = "SAMLResponse"
REQUEST_KEY_RELAY_STATE = "RelayState"

SESSION_KEY_AUTH_N_REQUEST = "authn_request"


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
