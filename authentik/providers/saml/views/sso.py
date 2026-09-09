"""authentik SAML IDP Views"""

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.events.models import Event, EventAction
from authentik.events.signals import get_login_event
from authentik.flows.apps import ContinuousLogin
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_SSO, FlowPlanner
from authentik.flows.views.executor import SESSION_KEY_POST
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.authn_request_parser import (
    AuthNRequest,
    AuthNRequestParser,
)
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_AUTH_N_REQUEST,
    REQUEST_KEY_RELAY_STATE,
    REQUEST_KEY_SAML_REQUEST,
    REQUEST_KEY_SAML_SIG_ALG,
    REQUEST_KEY_SAML_SIGNATURE,
    SAMLFlowFinalView,
)
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)

LOGGER = get_logger()

SESSION_KEY_LAST_LOGIN_UID = "authentik/providers/saml/last_login_uid"


class SAMLSSOView(PolicyAccessView):
    """SAML SSO Base View, which plans a flow and injects our final stage.
    Calls get/post handler."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan_context = {}

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["application_slug"])
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )

    def check_saml_request(self) -> HttpRequest | None:
        """Handler to verify the SAML Request. Must be implemented by a subclass"""
        raise NotImplementedError

    def get_resume_url(self) -> str | None:
        """URL to re-enter this SAML request after another tab authenticated."""
        return None

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Verify the SAML Request, and if valid initiate the FlowPlanner for the application"""
        # Call the method handler, which checks the SAML
        # Request and returns a HTTP Response on error
        method_response = self.check_saml_request()
        if method_response:
            return method_response
        # If the SP requested ForceAuthn, we must re-authenticate the user regardless of
        # any existing session, mirroring the OIDC provider's prompt=login handling.
        auth_n_request: AuthNRequest | None = self.plan_context.get(
            PLAN_CONTEXT_SAML_AUTH_N_REQUEST
        )
        if auth_n_request and auth_n_request.force_authn:
            reauth_response = self.check_force_authn(request)
            if reauth_response:
                return reauth_response
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                request,
                {
                    PLAN_CONTEXT_SSO: True,
                    PLAN_CONTEXT_APPLICATION: self.application,
                    PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
                    % {"application": self.application.name},
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: [],
                    **self.plan_context,
                },
            )
        except FlowNonApplicableException:
            raise Http404 from None
        plan.append_stage(in_memory_stage(SAMLFlowFinalView))
        return plan.to_redirect(
            request,
            self.provider.authorization_flow,
            next=self.get_resume_url(),
            allowed_silent_types=(
                [SAMLFlowFinalView]
                if self.provider.sp_binding in [SAMLBindings.REDIRECT] and not ContinuousLogin.get()
                else []
            ),
        )

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """GET and POST use the same handler, but we can't
        override .dispatch easily because PolicyAccessView's dispatch"""
        return self.get(request, application_slug)

    def check_force_authn(self, request: HttpRequest) -> HttpResponse | None:
        """Trigger re-authentication when the AuthnRequest carries ForceAuthn. Returns a
        redirect into the authentication flow if re-auth is still required, otherwise
        None to let the SSO flow proceed."""
        login_event = get_login_event(request)
        login_uid = str(login_event.pk) if login_event else None
        # Re-authenticate if it hasn't happened yet: either we have no record of a forced
        # login for this session, or the session's login event still matches the one we
        # saw before redirecting to the authentication flow. Once the user re-logs in, a
        # new login event is created, the UID changes, and we stop forcing re-auth.
        if (
            SESSION_KEY_LAST_LOGIN_UID not in request.session
            or login_uid == request.session[SESSION_KEY_LAST_LOGIN_UID]
        ):
            request.session[SESSION_KEY_LAST_LOGIN_UID] = login_uid
            return self.handle_no_permission()
        return None


class SAMLSSOBindingRedirectView(SAMLSSOView):
    """SAML Handler for SSO/Redirect bindings, which are sent via GET"""

    def get_resume_url(self) -> str | None:
        return self.request.get_full_path()

    def check_saml_request(self) -> HttpRequest | None:
        """Handle REDIRECT bindings"""
        if REQUEST_KEY_SAML_REQUEST not in self.request.GET:
            LOGGER.info("SAML payload missing")
            return bad_request_message(self.request, "The SAML request payload is missing.")

        try:
            auth_n_request = AuthNRequestParser(self.provider).parse_detached(
                self.request.GET[REQUEST_KEY_SAML_REQUEST],
                self.request.GET.get(REQUEST_KEY_RELAY_STATE),
                self.request.GET.get(REQUEST_KEY_SAML_SIGNATURE),
                self.request.GET.get(REQUEST_KEY_SAML_SIG_ALG),
            )
            self.plan_context[PLAN_CONTEXT_SAML_AUTH_N_REQUEST] = auth_n_request
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
class SAMLSSOBindingPOSTView(SAMLSSOView):
    """SAML Handler for SSO/POST bindings"""

    def check_saml_request(self) -> HttpRequest | None:
        """Handle POST bindings"""
        payload = self.request.POST
        # Restore the post body from the session
        # This happens when using POST bindings but the user isn't logged in
        # (user gets redirected and POST body is 'lost')
        if SESSION_KEY_POST in self.request.session:
            payload = self.request.session.pop(SESSION_KEY_POST)
        if REQUEST_KEY_SAML_REQUEST not in payload:
            LOGGER.info("SAML payload missing")
            return bad_request_message(self.request, "The SAML request payload is missing.")

        try:
            auth_n_request = AuthNRequestParser(self.provider).parse(
                payload[REQUEST_KEY_SAML_REQUEST],
                payload.get(REQUEST_KEY_RELAY_STATE),
            )
            self.plan_context[PLAN_CONTEXT_SAML_AUTH_N_REQUEST] = auth_n_request
        except CannotHandleAssertion as exc:
            LOGGER.info(str(exc))
            return bad_request_message(self.request, str(exc))
        return None


class SAMLSSOBindingInitView(SAMLSSOView):
    """SAML Handler for for IdP Initiated login flows"""

    def check_saml_request(self) -> HttpRequest | None:
        """Create SAML Response from scratch"""
        LOGGER.debug("No SAML Request, using IdP-initiated flow.")
        auth_n_request = AuthNRequestParser(self.provider).idp_initiated()
        self.plan_context[PLAN_CONTEXT_SAML_AUTH_N_REQUEST] = auth_n_request
