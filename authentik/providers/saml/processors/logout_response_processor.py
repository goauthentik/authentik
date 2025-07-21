"""LogoutResponse processor"""

import xmlsec
from lxml import etree
from lxml.etree import Element, SubElement

from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request_parser import LogoutRequest
from authentik.providers.saml.utils import get_random_id
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
    _issue_instant: str
    _response_id: str

    def __init__(self, provider: SAMLProvider, logout_request: LogoutRequest):
        self.provider = provider
        self.logout_request = logout_request
        self._issue_instant = get_time_string()
        self._response_id = get_random_id()

    def get_issuer(self) -> Element:
        """Get Issuer element"""
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer")
        issuer.text = self.provider.issuer
        return issuer

    def get_response(self, status: str = "Success", destination: str | None = None) -> Element:
        """Generate LogoutResponse XML"""
        response = Element(f"{{{NS_SAML_PROTOCOL}}}LogoutResponse", nsmap=NS_MAP)
        response.attrib["Version"] = "2.0"
        response.attrib["IssueInstant"] = self._issue_instant
        response.attrib["ID"] = self._response_id

        if destination:
            response.attrib["Destination"] = destination

        if self.logout_request.id:
            response.attrib["InResponseTo"] = self.logout_request.id

        response.append(self.get_issuer())

        # Add Status element
        status_element = SubElement(response, f"{{{NS_SAML_PROTOCOL}}}Status")
        status_code = SubElement(status_element, f"{{{NS_SAML_PROTOCOL}}}StatusCode")
        status_code.attrib["Value"] = f"urn:oasis:names:tc:SAML:2.0:status:{status}"

        # Add signature if configured
        if self.provider.signing_kp:
            self._add_signature(response)

        return response

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

    def build_response(self, status: str = "Success", destination: str | None = None) -> str:
        """Build and sign the response, return as string"""
        response = self.get_response(status, destination)

        if self.provider.signing_kp:
            self._sign_response(response)

        return etree.tostring(response, encoding="unicode", pretty_print=False)

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
