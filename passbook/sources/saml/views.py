"""saml sp views"""
from django.contrib.auth import login, logout
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from signxml.util import strip_pem_header

from passbook.lib.views import bad_request_message
from passbook.providers.saml.utils import get_random_id, render_xml
from passbook.providers.saml.utils.encoding import nice64
from passbook.providers.saml.utils.time import get_time_string
from passbook.sources.saml.exceptions import (
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from passbook.sources.saml.models import SAMLSource
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
        sso_destination = request.GET.get("next", None)
        request.session["sso_destination"] = sso_destination
        parameters = {
            "ACS_URL": build_full_url("acs", request, source),
            "DESTINATION": source.idp_url,
            "AUTHN_REQUEST_ID": get_random_id(),
            "ISSUE_INSTANT": get_time_string(),
            "ISSUER": get_issuer(request, source),
        }
        authn_req = get_authnrequest_xml(parameters, signed=False)
        _request = nice64(str.encode(authn_req))
        return render(
            request,
            "saml/sp/login.html",
            {
                "request_url": source.idp_url,
                "request": _request,
                "token": sso_destination,
                "source": source,
            },
        )


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

        try:
            user = processor.get_user()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect(reverse("passbook_core:overview"))
        except UnsupportedNameIDFormat as exc:
            return bad_request_message(request, str(exc))


class SLOView(View):
    """Single-Logout-View"""

    def dispatch(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        """Replies with an XHTML SSO Request."""
        source: SAMLSource = get_object_or_404(SAMLSource, slug=source_slug)
        if not source.enabled:
            raise Http404
        logout(request)
        return render(
            request,
            "saml/sp/sso_single_logout.html",
            {
                "idp_logout_url": source.idp_logout_url,
                "autosubmit": source.auto_logout,
            },
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
