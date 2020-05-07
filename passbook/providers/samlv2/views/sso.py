"""Single Signon Views"""
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest

from passbook.providers.samlv2.saml.constants import REQ_KEY_REQUEST, REQ_KEY_SIGNATURE
from passbook.providers.samlv2.saml.parser import SAMLRequest
from passbook.providers.samlv2.views.base import BaseSAMLView

# SAML Authentication flow in passbook
# - Parse and Verify SAML Request
# - Check access to application (this is done after parsing as it might take a few seconds)
# - Ask for user authorization (if required from Application)
# - Log Access to audit log
# - Create response with unique ID to protect against replay


class SAMLPostBindingView(BaseSAMLView):
    """Handle SAML POST-type Requests"""

    # pylint: disable=unused-argument
    def post(self, request: HttpRequest, app_slug: str) -> HttpResponse:
        """Handle POST Requests"""
        if REQ_KEY_REQUEST not in request.POST:
            return HttpResponseBadRequest()
        raw_saml_request = request.POST.get(REQ_KEY_REQUEST)
        detached_signature = request.POST.get(REQ_KEY_SIGNATURE, None)
        srq = SAMLRequest.parse(raw_saml_request, detached_signature)
        return self.handle_saml_request(srq)


class SAMLRedirectBindingView(BaseSAMLView):
    """Handle SAML Redirect-type Requests"""

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, app_slug: str) -> HttpResponse:
        """Handle GET Requests"""
        if REQ_KEY_REQUEST not in request.GET:
            return HttpResponseBadRequest()
        raw_saml_request = request.GET.get(REQ_KEY_REQUEST)
        detached_signature = request.GET.get(REQ_KEY_SIGNATURE, None)
        srq = SAMLRequest.parse(raw_saml_request, detached_signature)
        return self.handle_saml_request(srq)
