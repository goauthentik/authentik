"""saml sp views"""
import base64

from defusedxml import ElementTree
from django.contrib.auth import login, logout
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from signxml.util import strip_pem_header

from passbook.providers.saml.utils import get_random_id, render_xml
from passbook.providers.saml.utils.encoding import nice64
from passbook.providers.saml.utils.time import get_time_string
from passbook.sources.saml.models import SAMLSource
from passbook.sources.saml.utils import (
    _get_user_from_response,
    build_full_url,
    get_issuer,
)
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
        # sso_session = request.POST.get('RelayState', None)
        data = request.POST.get("SAMLResponse", None)
        response = base64.b64decode(data)
        root = ElementTree.fromstring(response)
        user = _get_user_from_response(root)
        # attributes = _get_attributes_from_response(root)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(reverse("passbook_core:overview"))


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
        cert_stripped = strip_pem_header(source.signing_cert.replace("\r", "")).replace(
            "\n", ""
        )
        return render_xml(
            request,
            "saml/sp/xml/sp_sso_descriptor.xml",
            {
                "acs_url": build_full_url("acs", request, source),
                "issuer": issuer,
                "cert_public_key": cert_stripped,
            },
        )
