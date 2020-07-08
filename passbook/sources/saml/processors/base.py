"""passbook saml source processor"""
from typing import TYPE_CHECKING, Dict

from defusedxml import ElementTree
from django.http import HttpRequest, HttpResponse
from signxml import XMLVerifier
from structlog import get_logger

from passbook.core.models import User
from passbook.flows.models import Flow
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
from passbook.sources.saml.processors.constants import (
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PRESISTENT,
    SAML_NAME_ID_FORMAT_TRANSIENT,
    SAML_NAME_ID_FORMAT_WINDOWS,
    SAML_NAME_ID_FORMAT_X509,
)
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

    def _handle_name_id_transient(self, request: HttpRequest) -> HttpResponse:
        """Handle a NameID with the Format of Transient. This is a bit more complex than other
        formats, as we need to create a temporary User that is used in the session. This
        user has an attribute that refers to our Source for cleanup. The user is also deleted
        on logout and periodically."""
        # Create a temporary User
        name_id = self._get_name_id().text
        user: User = User.objects.create(
            username=name_id,
            attributes={
                "saml": {"source": self._source.pk.hex, "delete_on_logout": True}
            },
        )
        LOGGER.debug("Created temporary user for NameID Transient", username=name_id)
        user.set_unusable_password()
        user.save()
        return self._flow_response(
            request,
            self._source.authentication_flow,
            **{
                PLAN_CONTEXT_PENDING_USER: user,
                PLAN_CONTEXT_AUTHENTICATION_BACKEND: DEFAULT_BACKEND,
            },
        )

    def _get_name_id(self) -> "Element":
        """Get NameID Element"""
        assertion = self._root.find("{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")
        subject = assertion.find("{urn:oasis:names:tc:SAML:2.0:assertion}Subject")
        name_id = subject.find("{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
        if name_id is None:
            raise ValueError("NameID Element not found!")
        return name_id

    def _get_name_id_filter(self) -> Dict[str, str]:
        """Returns the subject's NameID as a Filter for the `User`"""
        name_id_el = self._get_name_id()
        name_id = name_id_el.text
        if not name_id:
            raise UnsupportedNameIDFormat("Subject's NameID is empty.")
        _format = name_id_el.attrib["Format"]
        if _format == SAML_NAME_ID_FORMAT_EMAIL:
            return {"email": name_id}
        if _format == SAML_NAME_ID_FORMAT_PRESISTENT:
            return {"username": name_id}
        if _format == SAML_NAME_ID_FORMAT_X509:
            # This attribute is statically set by the LDAP source
            return {"attributes__distinguishedName": name_id}
        if _format == SAML_NAME_ID_FORMAT_WINDOWS:
            if "\\" in name_id:
                name_id = name_id.split("\\")[1]
            return {"username": name_id}
        raise UnsupportedNameIDFormat(
            f"Assertion contains NameID with unsupported format {_format}."
        )

    def prepare_flow(self, request: HttpRequest) -> HttpResponse:
        """Prepare flow plan depending on whether or not the user exists"""
        name_id = self._get_name_id()
        # Sanity check, show a warning if NameIDPolicy doesn't match what we go
        if self._source.name_id_policy != name_id.attrib["Format"]:
            LOGGER.warning(
                "NameID from IdP doesn't match our policy",
                expected=self._source.name_id_policy,
                got=name_id.attrib["Format"],
            )
        # transient NameIDs are handeled seperately as they don't have to go through flows.
        if name_id.attrib["Format"] == SAML_NAME_ID_FORMAT_TRANSIENT:
            return self._handle_name_id_transient(request)

        name_id_filter = self._get_name_id_filter()
        matching_users = User.objects.filter(**name_id_filter)
        if matching_users.exists():
            # User exists already, switch to authentication flow
            return self._flow_response(
                request,
                self._source.authentication_flow,
                **{
                    PLAN_CONTEXT_PENDING_USER: matching_users.first(),
                    PLAN_CONTEXT_AUTHENTICATION_BACKEND: DEFAULT_BACKEND,
                },
            )
        return self._flow_response(
            request,
            self._source.enrollment_flow,
            **{PLAN_CONTEXT_PROMPT: name_id_filter},
        )

    def _flow_response(
        self, request: HttpRequest, flow: Flow, **kwargs
    ) -> HttpResponse:
        kwargs[PLAN_CONTEXT_SSO] = True
        request.session[SESSION_KEY_PLAN] = FlowPlanner(flow).plan(request, kwargs)
        return redirect_with_qs(
            "passbook_flows:flow-executor-shell", request.GET, flow_slug=flow.slug,
        )
