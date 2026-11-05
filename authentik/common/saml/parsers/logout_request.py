"""LogoutRequest parser"""

from base64 import b64decode
from dataclasses import dataclass
from xml.etree.ElementTree import ParseError  # nosec

from defusedxml import ElementTree
from structlog.stdlib import get_logger

from authentik.common.saml.constants import NS_SAML_ASSERTION, NS_SAML_PROTOCOL
from authentik.common.saml.exceptions import ERROR_CANNOT_DECODE_REQUEST, CannotHandleAssertion
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate

LOGGER = get_logger()


@dataclass(slots=True)
class LogoutRequest:
    """Logout Request"""

    id: str | None = None

    issuer: str | None = None

    name_id: str | None = None

    name_id_format: str | None = None

    session_index: str | None = None

    relay_state: str | None = None


class LogoutRequestParser:
    """LogoutRequest Parser"""

    def _parse_xml(self, decoded_xml: str | bytes, relay_state: str | None = None) -> LogoutRequest:
        try:
            root = ElementTree.fromstring(decoded_xml)
        except (ParseError, ValueError) as exc:
            LOGGER.warning("Failed to parse SAML logout request", exc=exc)
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST) from exc
        # `ID` is a required attribute of every SAML request (SAML 2.0 core §3.2.1)
        if "ID" not in root.attrib:
            LOGGER.warning("SAML logout request is missing the ID attribute")
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST)
        request = LogoutRequest(
            id=root.attrib["ID"],
        )
        # Try both namespaces for Issuer
        issuers = root.findall(f"{{{NS_SAML_PROTOCOL}}}Issuer")
        if not issuers:
            issuers = root.findall(f"{{{NS_SAML_ASSERTION}}}Issuer")
        if len(issuers) > 0:
            request.issuer = issuers[0].text

        # Extract NameID
        name_ids = root.findall(f"{{{NS_SAML_ASSERTION}}}NameID")
        if not name_ids:
            name_ids = root.findall(f"{{{NS_SAML_PROTOCOL}}}NameID")
        if len(name_ids) > 0:
            request.name_id = name_ids[0].text
            # Extract NameID Format if present
            if "Format" in name_ids[0].attrib:
                request.name_id_format = name_ids[0].attrib["Format"]

        # Extract SessionIndex
        session_indexes = root.findall(f"{{{NS_SAML_PROTOCOL}}}SessionIndex")
        if not session_indexes:
            session_indexes = root.findall(f"{{{NS_SAML_ASSERTION}}}SessionIndex")
        if len(session_indexes) > 0:
            request.session_index = session_indexes[0].text

        request.relay_state = relay_state
        return request

    def parse(self, saml_request: str, relay_state: str | None = None) -> LogoutRequest:
        """Validate and parse raw request with enveloped signautre."""
        try:
            decoded_xml = b64decode(saml_request.encode())
        except ValueError as exc:
            LOGGER.warning("Failed to decode SAML logout request", exc=exc)
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST) from exc
        return self._parse_xml(decoded_xml, relay_state)

    def parse_detached(
        self,
        saml_request: str,
        relay_state: str | None = None,
    ) -> LogoutRequest:
        """Validate and parse raw request with detached signature"""
        try:
            decoded_xml = decode_base64_and_inflate(saml_request)
        except ValueError as exc:
            LOGGER.warning("Failed to decode SAML logout request", exc=exc)
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST) from exc

        return self._parse_xml(decoded_xml, relay_state)
