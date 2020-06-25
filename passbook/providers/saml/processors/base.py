"""Basic SAML Processor"""
from types import GeneratorType
from typing import TYPE_CHECKING, Dict, List, Union

from cryptography.exceptions import InvalidSignature
from defusedxml import ElementTree
from django.http import HttpRequest
from signxml import XMLVerifier
from structlog import get_logger

from passbook.core.exceptions import PropertyMappingExpressionException
from passbook.providers.saml.exceptions import CannotHandleAssertion
from passbook.providers.saml.processors.types import SAMLResponseParams
from passbook.providers.saml.utils import get_random_id
from passbook.providers.saml.utils.encoding import decode_base64_and_inflate, nice64
from passbook.providers.saml.utils.time import get_time_string, timedelta_from_string
from passbook.providers.saml.utils.xml_render import get_assertion_xml, get_response_xml

if TYPE_CHECKING:
    from passbook.providers.saml.models import SAMLProvider


# pylint: disable=too-many-instance-attributes
class Processor:
    """Base SAML 2.0 Auth-N-Request to Response Processor.
    Sub-classes should provide Service Provider-specific functionality."""

    is_idp_initiated = False

    _remote: "SAMLProvider"
    _http_request: HttpRequest

    _assertion_xml: str
    _response_xml: str
    _saml_response: str

    _relay_state: str
    _saml_request: str

    _assertion_params: Dict[str, Union[str, List[Dict[str, str]]]]
    _request_params: Dict[str, str]
    _response_params: Dict[str, str]

    @property
    def subject_format(self) -> str:
        """Get subject Format"""
        return "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"

    def __init__(self, remote: "SAMLProvider"):
        self.name = remote.name
        self._remote = remote
        self._logger = get_logger()

    def _build_assertion(self):
        """Builds _assertion_params."""
        self._assertion_params = {
            "ASSERTION_ID": get_random_id(),
            "ASSERTION_SIGNATURE": "",  # it's unsigned
            "AUDIENCE": self._remote.audience,
            "AUTH_INSTANT": get_time_string(),
            "ISSUE_INSTANT": get_time_string(),
            "NOT_BEFORE": get_time_string(
                timedelta_from_string(self._remote.assertion_valid_not_before)
            ),
            "NOT_ON_OR_AFTER": get_time_string(
                timedelta_from_string(self._remote.assertion_valid_not_on_or_after)
            ),
            "SESSION_INDEX": self._http_request.session.session_key,
            "SESSION_NOT_ON_OR_AFTER": get_time_string(
                timedelta_from_string(self._remote.session_valid_not_on_or_after)
            ),
            "SP_NAME_QUALIFIER": self._remote.audience,
            "SUBJECT": self._http_request.user.email,
            "SUBJECT_FORMAT": self.subject_format,
            "ISSUER": self._remote.issuer,
        }
        self._assertion_params.update(self._request_params)

    def _build_response(self):
        """Builds _response_params."""
        self._response_params = {
            "ASSERTION": self._assertion_xml,
            "ISSUE_INSTANT": get_time_string(),
            "RESPONSE_ID": get_random_id(),
            "RESPONSE_SIGNATURE": "",  # initially unsigned
            "ISSUER": self._remote.issuer,
        }
        self._response_params.update(self._request_params)

    def _encode_response(self):
        """Encodes _response_xml to _encoded_xml."""
        self._saml_response = nice64(str.encode(self._response_xml))

    def _extract_saml_request(self):
        """Retrieves the _saml_request AuthnRequest from the _http_request."""
        self._saml_request = self._http_request.session["SAMLRequest"]
        self._relay_state = self._http_request.session["RelayState"]

    def _format_assertion(self):
        """Formats _assertion_params as _assertion_xml."""
        # https://commons.lbl.gov/display/IDMgmt/Attribute+Definitions
        attributes = []
        from passbook.providers.saml.models import SAMLPropertyMapping

        for mapping in self._remote.property_mappings.all().select_subclasses():
            if not isinstance(mapping, SAMLPropertyMapping):
                continue
            try:
                mapping: SAMLPropertyMapping
                value = mapping.evaluate(
                    user=self._http_request.user,
                    request=self._http_request,
                    provider=self._remote,
                )
                if value is None:
                    continue
                mapping_payload = {
                    "Name": mapping.saml_name,
                    "FriendlyName": mapping.friendly_name,
                }
                # Normal values and arrays need different dict keys as they are handeled
                # differently in the template
                if isinstance(value, list):
                    mapping_payload["ValueArray"] = value
                elif isinstance(value, GeneratorType):
                    mapping_payload["ValueArray"] = list(value)
                else:
                    mapping_payload["Value"] = value
                attributes.append(mapping_payload)
            except PropertyMappingExpressionException as exc:
                self._logger.warning(exc)
                continue
        self._assertion_params["ATTRIBUTES"] = attributes
        self._assertion_xml = get_assertion_xml(
            "providers/saml/xml/assertions/generic.xml",
            self._assertion_params,
            signed=True,
        )

    def _format_response(self):
        """Formats _response_params as _response_xml."""
        assertion_id = self._assertion_params["ASSERTION_ID"]
        self._response_xml = get_response_xml(
            self._response_params, saml_provider=self._remote, assertion_id=assertion_id
        )

    def _get_saml_response_params(self) -> SAMLResponseParams:
        """Returns a dictionary of parameters for the response template."""
        return SAMLResponseParams(
            acs_url=self._request_params["ACS_URL"],
            saml_response=self._saml_response,
            relay_state=self._relay_state,
        )

    def _decode_and_parse_request(self):
        """Parses various parameters from _request_xml into _request_params."""
        decoded_xml = decode_base64_and_inflate(self._saml_request)

        if self._remote.require_signing and self._remote.signing_kp:
            self._logger.debug("Verifying Request signature")
            try:
                XMLVerifier().verify(
                    decoded_xml, x509_cert=self._remote.signing_kp.certificate_data
                )
            except InvalidSignature as exc:
                raise CannotHandleAssertion("Failed to verify signature") from exc

        root = ElementTree.fromstring(decoded_xml)

        params = {}
        params["ACS_URL"] = root.attrib.get(
            "AssertionConsumerServiceURL", self._remote.acs_url
        )
        params["REQUEST_ID"] = root.attrib["ID"]
        params["DESTINATION"] = root.attrib.get("Destination", "")
        params["PROVIDER_NAME"] = root.attrib.get("ProviderName", "")
        self._request_params = params

    def _validate_request(self):
        """
        Validates the SAML request against the SP configuration of this
        processor. Sub-classes should override this and raise a
        `CannotHandleAssertion` exception if the validation fails.

        Raises:
            CannotHandleAssertion: if the ACS URL specified in the SAML request
                doesn't match the one specified in the processor config.
        """
        request_acs_url = self._request_params["ACS_URL"]

        if self._remote.acs_url != request_acs_url:
            msg = (
                f"ACS URL of {request_acs_url} doesn't match Provider "
                f"ACS URL of {self._remote.acs_url}."
            )
            self._logger.info(msg)
            raise CannotHandleAssertion(msg)

    def can_handle(self, request: HttpRequest) -> bool:
        """Returns true if this processor can handle this request."""
        self._http_request = request
        # Read the request.
        try:
            self._extract_saml_request()
        except KeyError:
            raise CannotHandleAssertion("Couldn't find SAML request in user session")

        try:
            self._decode_and_parse_request()
        except Exception as exc:
            raise CannotHandleAssertion(f"Couldn't parse SAML request: {exc}") from exc

        self._validate_request()
        return True

    def generate_response(self) -> SAMLResponseParams:
        """Processes request and returns template variables suitable for a response."""
        # Build the assertion and response.
        # Only call can_handle if SP initiated Request, otherwise we have no Request
        if not self.is_idp_initiated:
            self.can_handle(self._http_request)

        self._build_assertion()
        self._format_assertion()
        self._build_response()
        self._format_response()
        self._encode_response()

        # Return proper template params.
        return self._get_saml_response_params()

    def init_deep_link(self, request: HttpRequest):
        """Initialize this Processor to make an IdP-initiated call to the SP's
        deep-linked URL."""
        self._http_request = request
        acs_url = self._remote.acs_url
        # NOTE: The following request params are made up. Some are blank,
        # because they comes over in the AuthnRequest, but we don't have an
        # AuthnRequest in this case:
        # - Destination: Should be this IdP's SSO endpoint URL. Not used in the response?
        # - ProviderName: According to the spec, this is optional.
        self._request_params = {
            "ACS_URL": acs_url,
            "DESTINATION": "",
            "PROVIDER_NAME": "",
        }
        self._relay_state = ""
