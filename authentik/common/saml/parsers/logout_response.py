"""LogoutResponse parser"""

import binascii
from base64 import b64decode
from dataclasses import dataclass
from xml.etree.ElementTree import ParseError  # nosec

from defusedxml import ElementTree

from authentik.common.saml.constants import NS_SAML_ASSERTION, NS_SAML_PROTOCOL, SAML_STATUS_SUCCESS
from authentik.common.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate

ERROR_CANNOT_DECODE_RESPONSE = "Cannot decode SAML response."


@dataclass(slots=True)
class LogoutResponse:
    """Logout Response"""

    id: str | None = None

    in_response_to: str | None = None

    issuer: str | None = None

    status: str | None = None

    relay_state: str | None = None


class LogoutResponseParser:
    """LogoutResponse Parser"""

    def _parse_xml(
        self, decoded_xml: str | bytes, relay_state: str | None = None
    ) -> LogoutResponse:
        try:
            root = ElementTree.fromstring(decoded_xml)
        except (ParseError, ValueError) as exc:
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_RESPONSE) from exc
        response = LogoutResponse(
            id=root.attrib.get("ID"),
            in_response_to=root.attrib.get("InResponseTo"),
        )

        # Try both namespaces for Issuer
        issuers = root.findall(f"{{{NS_SAML_ASSERTION}}}Issuer")
        if not issuers:
            issuers = root.findall(f"{{{NS_SAML_PROTOCOL}}}Issuer")
        if len(issuers) > 0:
            response.issuer = issuers[0].text

        # Extract Status
        status_elements = root.findall(f"{{{NS_SAML_PROTOCOL}}}Status")
        if len(status_elements) > 0:
            status_codes = status_elements[0].findall(f"{{{NS_SAML_PROTOCOL}}}StatusCode")
            if len(status_codes) > 0:
                response.status = status_codes[0].attrib.get("Value")

        response.relay_state = relay_state
        return response

    def parse(self, saml_response: str, relay_state: str | None = None) -> LogoutResponse:
        """Parse raw response with enveloped signature (POST binding)"""
        try:
            decoded_xml = b64decode(saml_response.encode())
        except UnicodeDecodeError, binascii.Error:
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_RESPONSE) from None
        return self._parse_xml(decoded_xml, relay_state)

    def parse_detached(self, saml_response: str, relay_state: str | None = None) -> LogoutResponse:
        """Parse raw response with detached signature (Redirect binding)"""
        try:
            decoded_xml = decode_base64_and_inflate(saml_response)
        except UnicodeDecodeError, binascii.Error:
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_RESPONSE) from None
        return self._parse_xml(decoded_xml, relay_state)

    def verify_status(self, response: LogoutResponse):
        """Verify that the LogoutResponse has a successful status."""
        if response.status != SAML_STATUS_SUCCESS:
            raise CannotHandleAssertion(f"LogoutResponse status is not success: {response.status}")
