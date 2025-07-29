"""SAML LogoutRequest Processor"""

import base64

import xmlsec
from lxml.etree import Element
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.utils import get_random_id
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode
from authentik.providers.saml.utils.time import get_time_string
from authentik.sources.saml.processors.constants import (
    DIGEST_ALGORITHM_TRANSLATION_MAP,
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_NAME_ID_FORMAT_EMAIL,
    SIGN_ALGORITHM_TRANSFORM_MAP,
)

LOGGER = get_logger()


class LogoutRequestProcessor:
    """Generate SAML LogoutRequest messages"""

    provider: SAMLProvider
    user: User
    destination: str
    name_id: str | None
    name_id_format: str
    relay_state: str | None

    _issue_instant: str
    _request_id: str

    def __init__(
        self,
        provider: SAMLProvider,
        user: User,
        destination: str,
        name_id: str | None = None,
        name_id_format: str = SAML_NAME_ID_FORMAT_EMAIL,
        relay_state: str | None = None,
    ):
        self.provider = provider
        self.user = user
        self.destination = destination
        self.name_id = name_id or user.email
        self.name_id_format = name_id_format
        self.relay_state = relay_state

        self._issue_instant = get_time_string()
        self._request_id = get_random_id()

    def get_issuer(self) -> Element:
        """Get Issuer element"""
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer")
        issuer.text = self.provider.issuer
        return issuer

    def get_name_id(self) -> Element:
        """Get NameID element"""
        name_id = Element(f"{{{NS_SAML_ASSERTION}}}NameID")
        name_id.attrib["Format"] = self.name_id_format
        name_id.text = self.name_id
        return name_id

    def build(self) -> Element:
        """Build a SAML LogoutRequest as etree Element"""
        logout_request = Element(f"{{{NS_SAML_PROTOCOL}}}LogoutRequest", nsmap=NS_MAP)
        logout_request.attrib["ID"] = self._request_id
        logout_request.attrib["Version"] = "2.0"
        logout_request.attrib["IssueInstant"] = self._issue_instant
        logout_request.attrib["Destination"] = self.destination

        logout_request.append(self.get_issuer())
        logout_request.append(self.get_name_id())

        LOGGER.debug(
            "Built LogoutRequest", request_id=self._request_id, destination=self.destination
        )
        return logout_request

    def encode_post(self) -> str:
        """Encode LogoutRequest for POST binding"""
        logout_request = self.build()
        if self.provider.signing_kp:
            self._sign_logout_request(logout_request)
        from lxml import etree  # nosec

        return base64.b64encode(etree.tostring(logout_request)).decode()

    def encode_redirect(self) -> str:
        """Encode LogoutRequest for Redirect binding"""
        logout_request = self.build()
        # Note: For redirect binding, signatures are added as query parameters, not in XML
        from lxml import etree  # nosec

        # Ensure proper XML serialization with encoding declaration
        xml_str = etree.tostring(logout_request, encoding="UTF-8", xml_declaration=True)
        return deflate_and_base64_encode(xml_str.decode("UTF-8"))

    def _sign_logout_request(self, logout_request: Element):
        """Sign the LogoutRequest element"""
        # Add signature structure
        signature_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
            self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha1
        )
        signature = xmlsec.template.create(
            logout_request,
            xmlsec.constants.TransformExclC14N,
            signature_algorithm_transform,
            ns=xmlsec.constants.DSigNs,
        )

        # Insert signature after Issuer element
        issuer = logout_request.find(f"{{{NS_SAML_ASSERTION}}}Issuer")
        if issuer is not None:
            issuer.addnext(signature)
        else:
            logout_request.insert(0, signature)

        # Sign the element
        self._sign(logout_request)

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
