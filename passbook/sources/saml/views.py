"""saml sp views"""
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from signxml import InvalidSignature
from signxml.util import strip_pem_header

from passbook.lib.views import bad_request_message
from passbook.providers.saml.utils import get_random_id, render_xml
from passbook.providers.saml.utils.encoding import deflate_and_base64_encode, nice64
from passbook.providers.saml.utils.time import get_time_string
from passbook.sources.saml.exceptions import (
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from passbook.sources.saml.models import SAMLBindingTypes, SAMLSource
from passbook.sources.saml.processors.base import Processor
from passbook.sources.saml.utils import build_full_url, get_issuer
from passbook.sources.saml.xml_render import get_authnrequest_xml


class InitiateView(View):
    """Get the Form with SAML Request, which sends us to the IDP"""

    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with an XHTML SSO Request."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404
        relay_state = request.GET.get("next", "")
        request.session["sso_destination"] = relay_state
        parameters = {
            "ACS_URL": build_full_url("acs", request, source),
            "DESTINATION": source.sso_url,
            "AUTHN_REQUEST_ID": get_random_id(),
            "ISSUE_INSTANT": get_time_string(),
            "ISSUER": get_issuer(request, source),
            "NAME_ID_POLICY": source.name_id_policy,
        }
        authn_req = get_authnrequest_xml(parameters, signed=False)
        # If the source is configured for Redirect bindings, we can just redirect there
        if source.binding_type == SAMLBindingTypes.Redirect:
            _request = deflate_and_base64_encode(authn_req.encode())
            url_args = urlencode({"SAMLRequest": _request, "RelayState": relay_state})
            return redirect(f"{source.sso_url}?{url_args}")
        # As POST Binding we show a form
        _request = nice64(authn_req.encode())
        if source.binding_type == SAMLBindingTypes.POST:
            return render(
                request,
                "saml/sp/login.html",
                {
                    "request_url": source.sso_url,
                    "request": _request,
                    "relay_state": relay_state,
                    "source": source,
                },
            )
        # Or an auto-submit form
        if source.binding_type == SAMLBindingTypes.POST_AUTO:
            return render(
                request,
                "generic/autosubmit_form.html",
                {
                    "title": _("Redirecting to %(app)s..." % {"app": source.name}),
                    "attrs": {"SAMLRequest": _request, "RelayState": relay_state},
                    "url": source.sso_url,
                },
            )
        raise Http404


@method_decorator(csrf_exempt, name="dispatch")
class ACSView(View):
    """AssertionConsumerService, consume assertion and log user in"""

    def post(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Handles a POSTed SSO Assertion and logs the user in."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404
        processor = Processor(source)
        try:
            processor.parse(request)
        except MissingSAMLResponse as exc:
            return bad_request_message(request, str(exc))
        except InvalidSignature as exc:
            return bad_request_message(request, str(exc))

        try:
            return processor.prepare_flow(request)
        except UnsupportedNameIDFormat as exc:
            return bad_request_message(request, str(exc))


class SLOView(LoginRequiredMixin, View):
    """Single-Logout-View"""

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with an XHTML SSO Request."""
        # TODO: Replace with flows
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404
        logout(request)
        return render(
            request,
            "saml/sp/sso_single_logout.html",
            {"idp_logout_url": source.slo_url},
        )


class MetadataView(View):
    """Return XML Metadata for IDP"""

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with the XML Metadata SPSSODescriptor."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        issuer = get_issuer(request, source)
        cert_stripped = strip_pem_header(
            source.signing_kp.certificate_data.replace("\r", "")
        ).replace("\n", "")
        return render_xml(
            request,
            "saml/sp/xml/sp_sso_descriptor.xml",
            {
                "acs_url": build_full_url("acs", request, source),
                "issuer": issuer,
                "cert_public_key": cert_stripped,
            },
        )
