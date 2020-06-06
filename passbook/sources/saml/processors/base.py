"""passbook saml source processor"""
from typing import TYPE_CHECKING, Optional

from defusedxml import ElementTree
from django.http import HttpRequest, HttpResponse
from signxml import XMLVerifier
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.providers.saml.utils.encoding import decode_base64_and_inflate
from passbook.sources.saml.exceptions import (
    MissingSAMLResponse,
    UnsupportedNameIDFormat,
)
from passbook.sources.saml.models import SAMLSource
from passbook.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from passbook.stages.prompt.stage import PLAN_CONTEXT_PROMPT

LOGGER = get_logger()
if TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec
DEFAULT_BACKEND = "django.contrib.auth.backends.ModelBackend"


class Processor:
    """SAML Response Processor"""

    _source: SAMLSource

    _root: "Element"
    _root_xml: str

    def __init__(self, source: SAMLSource):
        self._source = source

    def parse(self, request: HttpRequest):
        """Check if `request` contains SAML Response data, parse and validate it."""
        # First off, check if we have any SAML Data at all.
        raw_response = request.POST.get("SAMLResponse", None)
        if not raw_response:
            raise MissingSAMLResponse("Request does not contain 'SAMLResponse'")
        # relay_state = request.POST.get('RelayState', None)
        # Check if response is compressed, b64 decode it
        self._root_xml = decode_base64_and_inflate(raw_response)
        self._root = ElementTree.fromstring(self._root_xml)
        # Verify signed XML
        self._verify_signed()

    def _verify_signed(self):
        """Verify SAML Response's Signature"""
        verifier = XMLVerifier()
        verifier.verify(
            self._root_xml, x509_cert=self._source.signing_kp.certificate_data
        )

    def _get_email(self) -> Optional[str]:
        """
        Returns the email out of the response.

        At present, response must pass the email address as the Subject, eg.:

        <saml:Subject>
                <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                            SPNameQualifier=""
                            >email@example.com</saml:NameID>
        """
        assertion = self._root.find("{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")
        subject = assertion.find("{urn:oasis:names:tc:SAML:2.0:assertion}Subject")
        name_id = subject.find("{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
        name_id_format = name_id.attrib["Format"]
        if name_id_format != "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress":
            raise UnsupportedNameIDFormat(
                f"Assertion contains NameID with unsupported format {name_id_format}."
            )
        return name_id.text

    def prepare_flow(self, request: HttpRequest) -> HttpResponse:
        """Prepare flow plan depending on whether or not the user exists"""
        email = self._get_email()
        matching_users = User.objects.filter(email=email)
        if matching_users.exists():
            # User exists already, switch to authentication flow
            flow = self._source.authentication_flow
            request.session[SESSION_KEY_PLAN] = FlowPlanner(flow).plan(
                request,
                {
                    # Data for authentication
                    PLAN_CONTEXT_PENDING_USER: matching_users.first(),
                    PLAN_CONTEXT_AUTHENTICATION_BACKEND: DEFAULT_BACKEND,
                    PLAN_CONTEXT_SSO: True,
                },
            )
        else:
            flow = self._source.enrollment_flow
            request.session[SESSION_KEY_PLAN] = FlowPlanner(flow).plan(
                request,
                {
                    # Data for enrollment
                    PLAN_CONTEXT_PROMPT: {"username": email, "email": email},
                    PLAN_CONTEXT_SSO: True,
                },
            )
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell", request.GET, flow_slug=flow.slug,
        )
