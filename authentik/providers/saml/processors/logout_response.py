"""SAML LogoutResponse Processor"""

import base64

import xmlsec
from lxml import etree
from lxml.etree import Element, SubElement
from structlog.stdlib import get_logger

from authentik.providers.saml.models import SAMLProvider
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

LOGGER = get_logger()


class LogoutResponseProcessor:
    """Generate SAML LogoutResponse messages"""

    provider: SAMLProvider
    request_id: str
    destination: str
    relay_state: str | None

    _issue_instant: str
    _response_id: str

    def __init__(
        self,
        provider: SAMLProvider,
        request_id: str,
        destination: str,
        relay_state: str | None = None,
    ):
        self.provider = provider
        self.request_id = request_id
        self.destination = destination
        self.relay_state = relay_state

        self._issue_instant = get_time_string()
        self._response_id = get_random_id()

    def get_issuer(self) -> Element:
        """Get Issuer element"""
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer")
        issuer.text = self.provider.issuer
        return issuer

    def get_status(
        self, status_code: str = "urn:oasis:names:tc:SAML:2.0:status:Success"
    ) -> Element:
        """Get Status element"""
        status = Element(f"{{{NS_SAML_PROTOCOL}}}Status")
        status_code_element = SubElement(status, f"{{{NS_SAML_PROTOCOL}}}StatusCode")
        status_code_element.attrib["Value"] = status_code
        return status

    def build(self, status_code: str = "urn:oasis:names:tc:SAML:2.0:status:Success") -> Element:
        """Build a SAML LogoutResponse as etree Element"""
        logout_response = Element(f"{{{NS_SAML_PROTOCOL}}}LogoutResponse", nsmap=NS_MAP)
        logout_response.attrib["ID"] = self._response_id
        logout_response.attrib["Version"] = "2.0"
        logout_response.attrib["IssueInstant"] = self._issue_instant
        logout_response.attrib["Destination"] = self.destination
        logout_response.attrib["InResponseTo"] = self.request_id

        logout_response.append(self.get_issuer())
        logout_response.append(self.get_status(status_code))

        LOGGER.debug(
            "Built LogoutResponse",
            response_id=self._response_id,
            request_id=self.request_id,
            destination=self.destination,
        )
        return logout_response

    def encode_post(self) -> str:
        """Encode LogoutResponse for POST binding"""
        logout_response = self.build()
        if self.provider.signing_kp:
            self._sign_logout_response(logout_response)
        return base64.b64encode(etree.tostring(logout_response)).decode()

    def encode_redirect(self) -> str:
        """Encode LogoutResponse for Redirect binding"""
        logout_response = self.build()
        # Note: For redirect binding, signatures are added as query parameters, not in XML
        return deflate_and_base64_encode(etree.tostring(logout_response).decode())

    def _sign_logout_response(self, logout_response: Element):
        """Sign the LogoutResponse element"""
        # Add signature structure
        signature_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
            self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha1
        )
        signature = xmlsec.template.create(
            logout_response,
            xmlsec.constants.TransformExclC14N,
            signature_algorithm_transform,
            ns=xmlsec.constants.DSigNs,
        )

        # Insert signature after Issuer element
        issuer = logout_response.find(f"{{{NS_SAML_ASSERTION}}}Issuer")
        if issuer is not None:
            issuer.addnext(signature)
        else:
            logout_response.insert(0, signature)

        # Sign the element
        self._sign(logout_response)

    def _sign(self, element: Element):
        """Sign an XML element based on the providers' configured signing settings"""
        digest_algorithm_transform = DIGEST_ALGORITHM_TRANSLATION_MAP.get(
            self.provider.digest_algorithm, xmlsec.constants.TransformSha1
        )
        xmlsec.tree.add_ids(element, ["ID"])
        signature_node = xmlsec.tree.find_node(element, xmlsec.constants.NodeSignature)
        ref = xmlsec.template.add_reference(
            signature_node,
            digest_algorithm_transform,
            uri="#" + element.attrib["ID"],
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)
        key_info = xmlsec.template.ensure_key_info(signature_node)
        xmlsec.template.add_x509_data(key_info)

        ctx = xmlsec.SignatureContext()

        key = xmlsec.Key.from_memory(
            self.provider.signing_kp.key_data,
            xmlsec.constants.KeyDataFormatPem,
            None,
        )
        key.load_cert_from_memory(
            self.provider.signing_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
        )
        ctx.key = key
        ctx.sign(signature_node)
