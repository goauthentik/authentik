"""Shared SAML LogoutResponse parser"""

from defusedxml.lxml import fromstring
from lxml.etree import _Element  # nosec
from structlog.stdlib import get_logger

from authentik.common.saml.constants import NS_SAML_PROTOCOL, SAML_STATUS_SUCCESS
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate

LOGGER = get_logger()


class LogoutResponseParser:
    """Parse and validate SAML LogoutResponse messages"""

    _root: _Element

    def __init__(self, raw_response: str):
        self._raw_response = raw_response

    def parse(self):
        """Decode and parse the LogoutResponse XML."""
        # decode_base64_and_inflate handles both deflate-compressed (Redirect binding)
        # and plain base64 (POST binding) responses
        response_xml = decode_base64_and_inflate(self._raw_response)
        self._root = fromstring(response_xml.encode())

    def verify_status(self) -> bool:
        """Check LogoutResponse status. Returns True if status is Success."""
        status = self._root.find(f"{{{NS_SAML_PROTOCOL}}}Status")
        if status is None:
            return True
        status_code = status.find(f"{{{NS_SAML_PROTOCOL}}}StatusCode")
        if status_code is None:
            return True
        status_value = status_code.attrib.get("Value", "")
        if status_value != SAML_STATUS_SUCCESS:
            LOGGER.warning(
                "LogoutResponse status is not Success",
                status=status_value,
            )
            return False
        return True
