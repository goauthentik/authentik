"""LogoutResponse processor"""

import base64
from urllib.parse import quote, urlencode

import xmlsec
from lxml import etree
from lxml.etree import Element, SubElement

from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request_parser import LogoutRequest
from authentik.providers.saml.utils import get_random_id
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode
from authentik.providers.saml.utils.time import get_time_string
from authentik.sources.saml.processors.constants import (
    DIGEST_ALGORITHM_TRANSLATION_MAP,
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SIGN_ALGORITHM_TRANSFORM_MAP,
)


class LogoutResponseProcessor:
    """Generate a SAML LogoutResponse"""

    provider: SAMLProvider
    logout_request: LogoutRequest
    destination: str | None
    relay_state: str | None
    _issue_instant: str
    _response_id: str

    def __init__(
        self,
        provider: SAMLProvider,
        logout_request: LogoutRequest,
        destination: str | None = None,
        relay_state: str | None = None,
    ):
        self.provider = provider
        self.logout_request = logout_request
        self.destination = destination
        self.relay_state = relay_state or (logout_request.relay_state if logout_request else None)
        self._issue_instant = get_time_string()
        self._response_id = get_random_id()

    def get_issuer(self) -> Element:
        """Get Issuer element"""
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer")
        issuer.text = self.provider.issuer
        return issuer

    def build(self, status: str = "Success") -> Element:
        """Build a SAML LogoutResponse as etree Element"""
        response = Element(f"{{{NS_SAML_PROTOCOL}}}LogoutResponse", nsmap=NS_MAP)
        response.attrib["Version"] = "2.0"
        response.attrib["IssueInstant"] = self._issue_instant
        response.attrib["ID"] = self._response_id

        if self.destination:
            response.attrib["Destination"] = self.destination

        if self.logout_request and self.logout_request.id:
            response.attrib["InResponseTo"] = self.logout_request.id

        response.append(self.get_issuer())

        # Add Status element
        status_element = SubElement(response, f"{{{NS_SAML_PROTOCOL}}}Status")
        status_code = SubElement(status_element, f"{{{NS_SAML_PROTOCOL}}}StatusCode")
        status_code.attrib["Value"] = f"urn:oasis:names:tc:SAML:2.0:status:{status}"

        return response

    def build_response(self, status: str = "Success") -> str:
        """Build and sign LogoutResponse, return as XML string (not encoded)"""
        response = self.build(status)
        if self.provider.signing_kp and self.provider.sign_logout_response:
            self._add_signature(response)
            self._sign_response(response)
        return etree.tostring(response).decode()

    def encode_post(self, status: str = "Success") -> str:
        """Encode LogoutResponse for POST binding"""
        response = self.build(status)
        if self.provider.signing_kp and self.provider.sign_logout_response:
            self._add_signature(response)
            self._sign_response(response)
        return base64.b64encode(etree.tostring(response)).decode()

    def encode_redirect(self, status: str = "Success") -> str:
        """Encode LogoutResponse for Redirect binding"""
        response = self.build(status)
        # Note: For redirect binding, signatures are added as query parameters, not in XML
        xml_str = etree.tostring(response, encoding="UTF-8", xml_declaration=True)
        return deflate_and_base64_encode(xml_str.decode("UTF-8"))

    def get_redirect_url(self, status: str = "Success") -> str:
        """Build complete logout response URL for redirect binding with signature if needed"""
        encoded_response = self.encode_redirect(status)
        params = {
            "SAMLResponse": encoded_response,
        }

        if self.relay_state:
            params["RelayState"] = self.relay_state

        if self.provider.signing_kp and self.provider.sign_logout_response:
            sig_alg = self.provider.signature_algorithm
            params["SigAlg"] = sig_alg

            # Build the string to sign
            query_string = self._build_signable_query_string(params)

            signature = self._sign_query_string(query_string)
            params["Signature"] = base64.b64encode(signature).decode()

        # Some SP's use query params on their sls endpoint
        if not self.destination:
            raise ValueError("destination is required for redirect URL")

        separator = "&" if "?" in self.destination else "?"
        return f"{self.destination}{separator}{urlencode(params)}"

    def _add_signature(self, element: Element):
        """Add signature placeholder to element"""
        sign_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
            self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha1
        )
        signature = xmlsec.template.create(
            element,
            xmlsec.constants.TransformExclC14N,
            sign_algorithm_transform,
            ns=xmlsec.constants.DSigNs,
        )
        element.insert(1, signature)  # Insert after Issuer

    def _sign_response(self, response: Element):
        """Sign the response element"""
        digest_algorithm_transform = DIGEST_ALGORITHM_TRANSLATION_MAP.get(
            self.provider.digest_algorithm, xmlsec.constants.TransformSha1
        )

        xmlsec.tree.add_ids(response, ["ID"])
        signature_node = xmlsec.tree.find_node(response, xmlsec.constants.NodeSignature)

        ref = xmlsec.template.add_reference(
            signature_node,
            digest_algorithm_transform,
            uri="#" + response.attrib["ID"],
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)
        key_info = xmlsec.template.ensure_key_info(signature_node)
        xmlsec.template.add_x509_data(key_info)

        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(
            self.provider.signing_kp.key_data,  # Use key_data for the private key
            xmlsec.constants.KeyDataFormatPem,
        )
        ctx.key.load_cert_from_memory(
            self.provider.signing_kp.certificate_data, xmlsec.constants.KeyDataFormatPem
        )
        ctx.sign(signature_node)

    def _build_signable_query_string(self, params: dict) -> str:
        """Build query string for signing (order matters per SAML spec)"""
        # SAML spec requires specific order: SAMLResponse, RelayState, SigAlg
        # Values must be URL-encoded individually before concatenation
        ordered = []
        if "SAMLResponse" in params:
            ordered.append(f"SAMLResponse={quote(params['SAMLResponse'], safe='')}")
        if "RelayState" in params:
            ordered.append(f"RelayState={quote(params['RelayState'], safe='')}")
        if "SigAlg" in params:
            ordered.append(f"SigAlg={quote(params['SigAlg'], safe='')}")
        return "&".join(ordered)

    def _sign_query_string(self, query_string: str) -> bytes:
        """Sign the query string for redirect binding"""
        signature_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
            self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha256
        )

        key = xmlsec.Key.from_memory(
            self.provider.signing_kp.key_data,
            xmlsec.constants.KeyDataFormatPem,
            None,
        )

        ctx = xmlsec.SignatureContext()
        ctx.key = key

        return ctx.sign_binary(query_string.encode("utf-8"), signature_algorithm_transform)
