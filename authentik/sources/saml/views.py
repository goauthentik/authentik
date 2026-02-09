"""saml sp views"""

from urllib.parse import parse_qsl, urlparse, urlunparse

from defusedxml.lxml import fromstring
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

from authentik.common.saml.constants import NS_SAML_PROTOCOL, SAML_STATUS_SUCCESS
from authentik.core.models import AuthenticatedSession
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
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.lib.views import bad_request_message
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate, nice64
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
from authentik.sources.saml.processors.logout_request import LogoutRequestProcessor
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
    """Single-Logout-View: sends LogoutRequest to IdP or handles LogoutResponse from IdP"""

    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Handle GET requests: either initiate SLO or handle LogoutResponse via redirect."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404

        # Check if this is a LogoutResponse from the IdP (redirect binding)
        if "SAMLResponse" in request.GET:
            return self._handle_logout_response(request, source, request.GET["SAMLResponse"])

        # Otherwise, initiate SP-initiated SLO
        return self._initiate_logout(request, source)

    def post(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Handle POST requests: LogoutResponse from the IdP via POST binding."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404

        if "SAMLResponse" in request.POST:
            return self._handle_logout_response(request, source, request.POST["SAMLResponse"])

        return bad_request_message(request, "Missing SAMLResponse")

    def _initiate_logout(self, request: HttpRequest, source: SAMLSource) -> HttpResponse:
        """Build and send a LogoutRequest to the IdP."""
        if not source.slo_url:
            # No SLO URL configured, just log out locally
            logout(request)
            return redirect("authentik_core:root-redirect")

        # Find SAMLSourceSession for the current user
        saml_session = None
        if request.user.is_authenticated:
            auth_session = AuthenticatedSession.from_request(request, request.user)
            if auth_session:
                saml_session = (
                    SAMLSourceSession.objects.filter(
                        source=source,
                        user=request.user,
                        session=auth_session,
                    )
                    .first()
                )

        if not saml_session:
            # No session data, log out locally and redirect to IdP SLO URL
            logout(request)
            return redirect(source.slo_url)

        # Build LogoutRequest
        relay_state = request.build_absolute_uri(
            source.build_full_url(request, view="slo")
        )
        processor = LogoutRequestProcessor(
            source=source,
            http_request=request,
            destination=source.slo_url,
            name_id=saml_session.name_id,
            name_id_format=saml_session.name_id_format,
            session_index=saml_session.session_index,
            relay_state=relay_state,
        )

        # Clean up the session record
        saml_session.delete()

        # Log out locally
        logout(request)

        if source.slo_binding == SAMLSLOBindingTypes.REDIRECT:
            return redirect(processor.get_redirect_url())

        # POST binding - return autosubmit form
        form_data = processor.get_post_form_data()
        autosubmit_html = (
            "<html><body onload=\"document.forms[0].submit()\">"
            f"<form method=\"post\" action=\"{source.slo_url}\">"
        )
        for key, value in form_data.items():
            autosubmit_html += f'<input type="hidden" name="{key}" value="{value}"/>'
        autosubmit_html += "<noscript><input type=\"submit\" value=\"Continue\"/></noscript>"
        autosubmit_html += "</form></body></html>"
        return HttpResponse(autosubmit_html)

    def _handle_logout_response(
        self, request: HttpRequest, source: SAMLSource, raw_response: str
    ) -> HttpResponse:
        """Parse and handle a LogoutResponse from the IdP."""
        try:
            # decode_base64_and_inflate handles both deflate-compressed (Redirect binding)
            # and plain base64 (POST binding) responses
            response_xml = decode_base64_and_inflate(raw_response)
            root = fromstring(response_xml.encode())
        except (ValueError, etree.XMLSyntaxError) as exc:
            LOGGER.warning("Failed to parse LogoutResponse", exc=exc)
            return redirect("authentik_core:root-redirect")

        # Check status
        status = root.find(f"{{{NS_SAML_PROTOCOL}}}Status")
        if status is not None:
            status_code = status.find(f"{{{NS_SAML_PROTOCOL}}}StatusCode")
            if status_code is not None:
                status_value = status_code.attrib.get("Value", "")
                if status_value != SAML_STATUS_SUCCESS:
                    LOGGER.warning(
                        "LogoutResponse status is not Success",
                        status=status_value,
                        source=source.name,
                    )

        # User is already logged out at this point, redirect to root
        return redirect("authentik_core:root-redirect")


class MetadataView(View):
    """Return XML Metadata for IDP"""

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with the XML Metadata SPSSODescriptor."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        metadata = MetadataProcessor(source, request).build_entity_descriptor()
        return HttpResponse(metadata, content_type="text/xml")
