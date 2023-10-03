"""LogoutRequest parser"""
from base64 import b64decode
from dataclasses import dataclass
from typing import Optional

from defusedxml import ElementTree

from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.authn_request_parser import ERROR_CANNOT_DECODE_REQUEST
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate
from authentik.sources.saml.processors.constants import NS_SAML_PROTOCOL


@dataclass(slots=True)
class LogoutRequest:
    """Logout Request"""

    id: Optional[str] = None

    issuer: Optional[str] = None

    relay_state: Optional[str] = None


class LogoutRequestParser:
    """LogoutRequest Parser"""

    provider: SAMLProvider

    def __init__(self, provider: SAMLProvider):
        """
        Initialize a LogoutRequestParser with a SAMLProvider.

        Parameters:
            provider (SAMLProvider): The SAML provider object.
        """
        self.provider = provider

    def _parse_xml(
        self, decoded_xml: str | bytes, relay_state: Optional[str] = None
    ) -> LogoutRequest:
        """
        Parse an XML string and return a LogoutRequest object.

        This method parses an XML string and constructs a LogoutRequest object
        using the parsed data.

        Parameters:
            decoded_xml (str | bytes): The XML string to parse.
            relay_state (Optional[str], optional): The relay state. Defaults to None.

        Returns:
            LogoutRequest: The parsed LogoutRequest object.
        """
        root = ElementTree.fromstring(decoded_xml)
        request = LogoutRequest(
            id=root.attrib["ID"],
        )
        issuers = root.findall(f"{{{NS_SAML_PROTOCOL}}}Issuer")
        if len(issuers) > 0:
            request.issuer = issuers[0].text
        request.relay_state = relay_state
        return request

    def parse(self, saml_request: str, relay_state: Optional[str] = None) -> LogoutRequest:
        """
        Validate and parse a raw request with an enveloped signature.

        This method decodes a SAML logout request, validates it, and calls
        the _parse_xml method to parse the request.

        Parameters:
            saml_request (str): The SAML logout request.
            relay_state (Optional[str], optional): The relay state. Defaults to None.

        Returns:
            LogoutRequest: The parsed LogoutRequest object.
        """
        try:
            decoded_xml = b64decode(saml_request.encode())
        except UnicodeDecodeError:
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST)
        return self._parse_xml(decoded_xml, relay_state)

    def parse_detached(
        self,
        saml_request: str,
        relay_state: Optional[str] = None,
    ) -> LogoutRequest:
        """
        Validate and parse a raw request with a detached signature.

        This method decodes a SAML logout request with a detached signature,
        validates it, and calls the _parse_xml method to parse the request.

        Parameters:
            saml_request (str): The SAML logout request.
            relay_state (Optional[str], optional): The relay state. Defaults to None.

        Returns:
            LogoutRequest: The parsed LogoutRequest object.
        """
        try:
            decoded_xml = decode_base64_and_inflate(saml_request)
        except UnicodeDecodeError:
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST)

        return self._parse_xml(decoded_xml, relay_state)
