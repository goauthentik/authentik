"""saml sp views"""

from urllib.parse import parse_qsl, urlparse, urlunparse

from django.contrib.auth import logout
from django.http import Http404, HttpRequest, HttpResponse
from django.http.response import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from lxml import etree  # nosec
from structlog.stdlib import get_logger
from xmlsec import InternalError, VerificationError

from authentik.common.saml.exceptions import CannotHandleAssertion
from authentik.common.saml.parsers.logout_request import LogoutRequestParser
from authentik.common.saml.parsers.logout_response import LogoutResponseParser
from authentik.flows.challenge import (
    PLAN_CONTEXT_ATTRS,
    PLAN_CONTEXT_TITLE,
    PLAN_CONTEXT_URL,
    AutosubmitChallenge,
    Challenge,
    ChallengeResponse,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_REDIRECT,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    FlowPlan,
    FlowPlanner,
)
from authentik.flows.stage import ChallengeStageView, RedirectStage, SessionEndStage
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.lib.views import bad_request_message
from authentik.providers.saml.utils.encoding import nice64
from authentik.sources.saml.exceptions import (
    InvalidSignature,
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from authentik.sources.saml.models import (
    SAMLBindingTypes,
    SAMLSLOBindingTypes,
    SAMLSource,
    SAMLSourceSession,
)
from authentik.sources.saml.processors.logout_response import LogoutResponseBuilder
from authentik.sources.saml.processors.metadata import MetadataProcessor
from authentik.sources.saml.processors.request import RequestProcessor
from authentik.sources.saml.processors.response import ResponseProcessor
from authentik.stages.consent.stage import PLAN_CONTEXT_CONSENT_HEADER, ConsentStageView

LOGGER = get_logger()


class AutosubmitStageView(ChallengeStageView):
    """Wrapper stage to create an autosubmit challenge from plan context variables"""

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return AutosubmitChallenge(
            data={
                "component": "ak-stage-autosubmit",
                "title": self.executor.plan.context.get(PLAN_CONTEXT_TITLE, ""),
                "url": self.executor.plan.context.get(PLAN_CONTEXT_URL, ""),
                "attrs": self.executor.plan.context.get(PLAN_CONTEXT_ATTRS, ""),
            },
        )

    # Since `ak-stage-autosubmit` redirects off site, we don't have anything to check
    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return HttpResponseBadRequest()


class InitiateView(View):
    """Get the Form with SAML Request, which sends us to the IDP"""

    def handle_login_flow(self, source: SAMLSource, *stages_to_append, **kwargs) -> HttpResponse:
        """Prepare Authentication Plan, redirect user FlowExecutor"""
        # Ensure redirect is carried through when user was trying to
        # authorize application
        final_redirect = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, "authentik_core:if-user"
        )
        kwargs.update(
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_SOURCE: source,
                PLAN_CONTEXT_REDIRECT: final_redirect,
            }
        )
        # We run the Flow planner here so we can pass the Pending user in the context
        planner = FlowPlanner(source.pre_authentication_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(self.request, kwargs)
        except FlowNonApplicableException:
            raise Http404 from None
        for stage in stages_to_append:
            plan.append_stage(stage)
        return plan.to_redirect(self.request, source.pre_authentication_flow)

    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with an XHTML SSO Request."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404
        relay_state = request.GET.get("next", "")
        auth_n_req = RequestProcessor(source, request, relay_state)
        # If the source is configured for Redirect bindings, we can just redirect there
        if source.binding_type == SAMLBindingTypes.REDIRECT:
            # Parse the initial SSO URL
            sso_url = urlparse(source.sso_url)
            # Parse the querystring into a dict...
            url_kwargs = dict(parse_qsl(sso_url.query))
            # ... and update it with the SAML args
            url_kwargs.update(auth_n_req.build_auth_n_detached())
            # Update the url
            final_url = urlunparse(sso_url._replace(query=urlencode(url_kwargs)))
            return redirect(final_url)
        # As POST Binding we show a form
        try:
            saml_request = nice64(auth_n_req.build_auth_n())
        except InternalError as exc:
            LOGGER.warning(str(exc))
            return bad_request_message(request, str(exc))
        injected_stages = []
        plan_kwargs = {
            PLAN_CONTEXT_TITLE: f"Redirecting to {source.name}...",
            PLAN_CONTEXT_ATTRS: {
                "SAMLRequest": saml_request,
                "RelayState": relay_state,
            },
            PLAN_CONTEXT_URL: source.sso_url,
        }
        # For just POST we add a consent stage,
        # otherwise we default to POST_AUTO, with direct redirect
        if source.binding_type == SAMLBindingTypes.POST:
            injected_stages.append(in_memory_stage(ConsentStageView))
            plan_kwargs[PLAN_CONTEXT_CONSENT_HEADER] = _(
                "Continue to {source_name}".format(source_name=source.name)
            )
        injected_stages.append(in_memory_stage(AutosubmitStageView))
        return self.handle_login_flow(
            source,
            *injected_stages,
            **plan_kwargs,
        )


@method_decorator(csrf_exempt, name="dispatch")
class ACSView(View):
    """AssertionConsumerService, consume assertion and log user in"""

    def post(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Handles a POSTed SSO Assertion and logs the user in."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404
        processor = ResponseProcessor(source, request)
        try:
            processor.parse()
        except (InvalidSignature, MissingSAMLResponse, VerificationError, ValueError) as exc:
            return bad_request_message(request, str(exc))

        try:
            if SESSION_KEY_PLAN in request.session:
                plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
                plan_redirect = plan.context.get(PLAN_CONTEXT_REDIRECT)
                if plan_redirect:
                    self.request.session[SESSION_KEY_GET] = {NEXT_ARG_NAME: plan_redirect}
            return processor.prepare_flow_manager().get_flow()
        except (UnsupportedNameIDFormat, ValueError) as exc:
            return bad_request_message(request, str(exc))


@method_decorator(csrf_exempt, name="dispatch")
class SLOView(View):
    """Single-Logout-View: handles SP-initiated SLO, IdP-initiated LogoutRequest,
    and LogoutResponse from IdP"""

    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Handle GET requests: LogoutResponse, LogoutRequest, or initiate SLO."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404

        if "SAMLResponse" in request.GET:
            return self._handle_logout_response(request.GET["SAMLResponse"])

        if "SAMLRequest" in request.GET:
            return self._handle_logout_request(
                request, source, request.GET["SAMLRequest"], is_post=False
            )

        # No SAML message, initiate SP-initiated SLO
        return self._initiate_logout(request)

    def post(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Handle POST requests: LogoutResponse or LogoutRequest from the IdP."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404

        if "SAMLResponse" in request.POST:
            return self._handle_logout_response(request.POST["SAMLResponse"])

        if "SAMLRequest" in request.POST:
            return self._handle_logout_request(
                request, source, request.POST["SAMLRequest"], is_post=True
            )

        return bad_request_message(request, "Missing SAMLRequest or SAMLResponse")

    def _initiate_logout(self, request: HttpRequest) -> HttpResponse:
        """Initiate logout using the brand's invalidation flow.

        The invalidation flow contains a UserLogoutStage which fires the
        flow_pre_user_logout signal. Our signal handler in signals.py picks that up,
        finds the SAMLSourceSession, and injects the SLO redirect/POST stage."""
        # Sources do not have an invalidation flow, use the brand's
        flow = request.brand.flow_invalidation
        if not flow:
            logout(request)
            return redirect("authentik_core:root-redirect")

        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(request)
        except FlowNonApplicableException:
            logout(request)
            return redirect("authentik_core:root-redirect")
        plan.append_stage(in_memory_stage(SessionEndStage))
        return plan.to_redirect(request, flow)

    def _handle_logout_request(
        self,
        request: HttpRequest,
        source: SAMLSource,
        raw_request: str,
        is_post: bool = False,
    ) -> HttpResponse:
        """Handle an incoming LogoutRequest from the IdP (IdP-initiated SLO).

        Parses the request, deletes the SAMLSourceSession (to prevent circular
        redirect back to the IdP), runs the invalidation flow, and appends a
        final stage to send the LogoutResponse back to the IdP."""
        parser = LogoutRequestParser()
        try:
            if is_post:
                logout_request = parser.parse(raw_request)
            else:
                logout_request = parser.parse_detached(raw_request)
        except (CannotHandleAssertion, ValueError) as exc:
            LOGGER.warning("Failed to parse LogoutRequest from IdP", exc=exc)
            return bad_request_message(request, str(exc))

        relay_state = (
            request.GET.get("RelayState") if not is_post else request.POST.get("RelayState")
        )

        # Delete SAMLSourceSession so the source signal handler doesn't try to
        # redirect back to the IdP (which would be circular)
        SAMLSourceSession.objects.filter(
            source=source,
            user=request.user,
        ).delete()

        # Build the LogoutResponse to send back to the IdP after logout
        response_builder = LogoutResponseBuilder(
            source=source,
            http_request=request,
            destination=source.slo_url,
            in_response_to=logout_request.id,
        )

        # Sources do not have an invalidation flow, use the brand's
        flow = request.brand.flow_invalidation
        if not flow:
            logout(request)
            return self._send_logout_response(response_builder, relay_state)

        planner = FlowPlanner(flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(request)
        except FlowNonApplicableException:
            logout(request)
            return self._send_logout_response(response_builder, relay_state)

        # Append logout response stage, then session end
        self._append_response_stage(plan, source, response_builder, relay_state)
        plan.append_stage(in_memory_stage(SessionEndStage))
        return plan.to_redirect(request, flow)

    def _send_logout_response(
        self,
        response_builder: LogoutResponseBuilder,
        relay_state: str | None = None,
    ) -> HttpResponse:
        """Send LogoutResponse back to the IdP directly (no flow).
        Without a flow we can't render an autosubmit form, so always redirect."""
        return redirect(response_builder.get_redirect_url(relay_state))

    def _append_response_stage(
        self,
        plan: FlowPlan,
        source: SAMLSource,
        response_builder: LogoutResponseBuilder,
        relay_state: str | None = None,
    ):
        """Append a stage to send the LogoutResponse back to the IdP."""
        if source.slo_binding == SAMLSLOBindingTypes.REDIRECT:
            redirect_url = response_builder.get_redirect_url(relay_state)
            plan.append_stage(in_memory_stage(RedirectStage, destination=redirect_url))
        else:
            # POST binding — use autosubmit form
            form_data = response_builder.get_post_form_data(relay_state)
            plan.context[PLAN_CONTEXT_TITLE] = f"Logging out of {source.name}..."
            plan.context[PLAN_CONTEXT_URL] = source.slo_url
            plan.context[PLAN_CONTEXT_ATTRS] = form_data
            plan.append_stage(in_memory_stage(AutosubmitStageView))

    def _handle_logout_response(self, raw_response: str) -> HttpResponse:
        """Parse and handle a LogoutResponse from the IdP."""
        processor = LogoutResponseParser(raw_response)
        try:
            processor.parse()
        except (ValueError, etree.XMLSyntaxError) as exc:
            LOGGER.warning("Failed to parse LogoutResponse", exc=exc)
            return redirect("authentik_core:root-redirect")

        processor.verify_status()

        # User is already logged out at this point, redirect to root
        return redirect("authentik_core:root-redirect")


class MetadataView(View):
    """Return XML Metadata for IDP"""

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with the XML Metadata SPSSODescriptor."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        metadata = MetadataProcessor(source, request).build_entity_descriptor()
        return HttpResponse(metadata, content_type="text/xml")
