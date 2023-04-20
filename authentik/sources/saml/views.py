"""saml sp views"""
from urllib.parse import parse_qsl, urlparse, urlunparse

from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.http.response import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger
from xmlsec import InternalError, VerificationError

from authentik.flows.challenge import (
    PLAN_CONTEXT_ATTRS,
    PLAN_CONTEXT_TITLE,
    PLAN_CONTEXT_URL,
    AutosubmitChallenge,
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_REDIRECT,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.lib.views import bad_request_message
from authentik.providers.saml.utils.encoding import nice64
from authentik.sources.saml.exceptions import MissingSAMLResponse, UnsupportedNameIDFormat
from authentik.sources.saml.models import SAMLBindingTypes, SAMLSource
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
                "type": ChallengeTypes.NATIVE.value,
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
            raise Http404
        for stage in stages_to_append:
            plan.append_stage(stage)
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=source.pre_authentication_flow.slug,
        )

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
            plan_kwargs[PLAN_CONTEXT_CONSENT_HEADER] = f"Continue to {source.name}"
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
        except MissingSAMLResponse as exc:
            return bad_request_message(request, str(exc))
        except VerificationError as exc:
            return bad_request_message(request, str(exc))

        try:
            return processor.prepare_flow_manager().get_flow()
        except (UnsupportedNameIDFormat, ValueError) as exc:
            return bad_request_message(request, str(exc))


class SLOView(LoginRequiredMixin, View):
    """Single-Logout-View"""

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Log user out and redirect them to the IdP's SLO URL."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404
        logout(request)
        return redirect(source.slo_url)


class MetadataView(View):
    """Return XML Metadata for IDP"""

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with the XML Metadata SPSSODescriptor."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        metadata = MetadataProcessor(source, request).build_entity_descriptor()
        return HttpResponse(metadata, content_type="text/xml")
