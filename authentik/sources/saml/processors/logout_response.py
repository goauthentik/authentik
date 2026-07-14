"""SAML Source LogoutResponse Builder"""

import base64
from urllib.parse import urlencode

from django.http import HttpRequest
from lxml import etree  # nosec
from lxml.etree import Element

from authentik.common.saml.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_STATUS_SUCCESS,
)
from authentik.providers.saml.utils import get_random_id
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode
from authentik.providers.saml.utils.time import get_time_string
from authentik.sources.saml.models import SAMLSource


class LogoutResponseBuilder:
    """Build SAML LogoutResponse messages for IdP-initiated logout"""

    source: SAMLSource
    http_request: HttpRequest
    destination: str
    in_response_to: str

    _issue_instant: str
    _response_id: str

    def __init__(
        self,
        source: SAMLSource,
        http_request: HttpRequest,
        destination: str,
        in_response_to: str,
    ):
        self.source = source
        self.http_request = http_request
        self.destination = destination
        self.in_response_to = in_response_to

        self._issue_instant = get_time_string()
        self._response_id = get_random_id()

    def build(self) -> Element:
        """Build a SAML LogoutResponse as etree Element"""
        response = Element(f"{{{NS_SAML_PROTOCOL}}}LogoutResponse", nsmap=NS_MAP)
        response.attrib["ID"] = self._response_id
        response.attrib["Version"] = "2.0"
        response.attrib["IssueInstant"] = self._issue_instant
        response.attrib["Destination"] = self.destination
        response.attrib["InResponseTo"] = self.in_response_to

        # Issuer
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer")
        issuer.text = self.source.get_issuer(self.http_request)
        response.append(issuer)

        # Status
        status = Element(f"{{{NS_SAML_PROTOCOL}}}Status")
        status_code = Element(f"{{{NS_SAML_PROTOCOL}}}StatusCode")
        status_code.attrib["Value"] = SAML_STATUS_SUCCESS
        status.append(status_code)
        response.append(status)

        return response

    def encode_post(self) -> str:
        """Encode LogoutResponse for POST binding"""
        response = self.build()
        return base64.b64encode(etree.tostring(response)).decode()

    def encode_redirect(self) -> str:
        """Encode LogoutResponse for Redirect binding"""
        response = self.build()
        xml_str = etree.tostring(response, encoding="UTF-8", xml_declaration=True)
        return deflate_and_base64_encode(xml_str.decode("UTF-8"))

    def get_redirect_url(self, relay_state: str | None = None) -> str:
        """Build complete URL for redirect binding"""
        encoded = self.encode_redirect()
        params = {"SAMLResponse": encoded}
        if relay_state:
            params["RelayState"] = relay_state
        separator = "&" if "?" in self.destination else "?"
        return f"{self.destination}{separator}{urlencode(params)}"

    def get_post_form_data(self, relay_state: str | None = None) -> dict:
        """Get form data for POST binding"""
        data = {"SAMLResponse": self.encode_post()}
        if relay_state:
            data["RelayState"] = relay_state
        return data
