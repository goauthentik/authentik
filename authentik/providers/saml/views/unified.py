"""Unified SAML endpoint - handles SSO and SLO based on message type"""

from base64 import b64decode

from defusedxml.lxml import fromstring
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.common.saml.constants import NS_MAP
from authentik.lib.views import bad_request_message
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate
from authentik.providers.saml.views.flows import (
    REQUEST_KEY_SAML_REQUEST,
    REQUEST_KEY_SAML_RESPONSE,
)
from authentik.providers.saml.views.sp_slo import (
    SPInitiatedSLOBindingPOSTView,
    SPInitiatedSLOBindingRedirectView,
)
from authentik.providers.saml.views.sso import (
    SAMLSSOBindingPOSTView,
    SAMLSSOBindingRedirectView,
)

LOGGER = get_logger()

# SAML message type constants
SAML_MESSAGE_TYPE_AUTHN_REQUEST = "AuthnRequest"
SAML_MESSAGE_TYPE_LOGOUT_REQUEST = "LogoutRequest"


def detect_saml_message_type(saml_request: str, is_post_binding: bool) -> str | None:
    """Parse SAML request to determine if AuthnRequest or LogoutRequest."""
    try:
        if is_post_binding:
            decoded_xml = b64decode(saml_request.encode())
        else:
            decoded_xml = decode_base64_and_inflate(saml_request)

        root = fromstring(decoded_xml)
        if len(root.xpath("//samlp:AuthnRequest", namespaces=NS_MAP)):
            return SAML_MESSAGE_TYPE_AUTHN_REQUEST
        if len(root.xpath("//samlp:LogoutRequest", namespaces=NS_MAP)):
            return SAML_MESSAGE_TYPE_LOGOUT_REQUEST
        return None
    except Exception:  # noqa: BLE001
        return None


@method_decorator(xframe_options_sameorigin, name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class SAMLUnifiedView(View):
    """Unified SAML endpoint - handles SSO and SLO based on message type.

    The operation type is determined by parsing
    the incoming SAML message:
    - AuthnRequest -> SSO flow (delegates to SAMLSSOBindingRedirectView/POSTView)
    - LogoutRequest -> SLO flow (delegates to SPInitiatedSLOBindingRedirectView/POSTView)
    - LogoutResponse -> SLO completion (delegates to SPInitiatedSLOBindingRedirectView/POSTView)
    """

    def dispatch(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Route the request based on SAML message type."""
        # Determine binding from HTTP method
        is_post_binding = request.method == "POST"
        data = request.POST if is_post_binding else request.GET

        # LogoutResponse - delegate to SLO view (handles it in dispatch)
        if REQUEST_KEY_SAML_RESPONSE in data:
            return self._delegate_to_slo(request, application_slug, is_post_binding)

        # Check for SAML request
        if REQUEST_KEY_SAML_REQUEST not in data:
            LOGGER.info("SAML payload missing")
            return bad_request_message(request, "The SAML request payload is missing.")

        # Detect message type and delegate
        saml_request = data[REQUEST_KEY_SAML_REQUEST]
        message_type = detect_saml_message_type(saml_request, is_post_binding)

        if message_type == SAML_MESSAGE_TYPE_AUTHN_REQUEST:
            return self._delegate_to_sso(request, application_slug, is_post_binding)
        elif message_type == SAML_MESSAGE_TYPE_LOGOUT_REQUEST:
            return self._delegate_to_slo(request, application_slug, is_post_binding)
        else:
            LOGGER.warning("Unknown SAML message type", message_type=message_type)
            return bad_request_message(
                request, f"Unsupported SAML message type: {message_type or 'unknown'}"
            )

    def _delegate_to_sso(
        self, request: HttpRequest, application_slug: str, is_post_binding: bool
    ) -> HttpResponse:
        """Delegate to the appropriate SSO view."""
        if is_post_binding:
            view = SAMLSSOBindingPOSTView.as_view()
        else:
            view = SAMLSSOBindingRedirectView.as_view()
        return view(request, application_slug=application_slug)

    def _delegate_to_slo(
        self, request: HttpRequest, application_slug: str, is_post_binding: bool
    ) -> HttpResponse:
        """Delegate to the appropriate SLO view."""
        if is_post_binding:
            view = SPInitiatedSLOBindingPOSTView.as_view()
        else:
            view = SPInitiatedSLOBindingRedirectView.as_view()
        return view(request, application_slug=application_slug)
