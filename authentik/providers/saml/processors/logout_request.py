"""SAML LogoutRequest Processor"""

import base64
from urllib.parse import quote, urlencode

import xmlsec
from lxml import etree  # nosec
from lxml.etree import Element, _Element

from authentik.common.saml.constants import (
    DIGEST_ALGORITHM_TRANSLATION_MAP,
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_NAME_ID_FORMAT_EMAIL,
    SIGN_ALGORITHM_TRANSFORM_MAP,
)
from authentik.core.models import User
from authentik.lib.xml import remove_xml_newlines
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.utils import get_random_id
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode
from authentik.providers.saml.utils.time import get_time_string


class LogoutRequestProcessor:
    """Generate SAML LogoutRequest messages"""

    provider: SAMLProvider
    user: User | None
    destination: str
    name_id: str | None
    name_id_format: str
    session_index: str | None
    relay_state: str | None

    _issue_instant: str
    _request_id: str

    def __init__(
        self,
        provider: SAMLProvider,
        user: User | None,
        destination: str,
        name_id: str | None = None,
        name_id_format: str = SAML_NAME_ID_FORMAT_EMAIL,
        session_index: str | None = None,
        relay_state: str | None = None,
    ):
        self.provider = provider
        self.user = user
        self.destination = destination
        self.name_id = name_id or (user.email if user else None)
        self.name_id_format = name_id_format
        self.session_index = session_index
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

        if self.session_index:
            session_index_element = Element(f"{{{NS_SAML_PROTOCOL}}}SessionIndex")
            session_index_element.text = self.session_index
            logout_request.append(session_index_element)

        return logout_request

    def encode_post(self) -> str:
        """Encode LogoutRequest for POST binding"""
        logout_request = self.build()
        if self.provider.signing_kp and self.provider.sign_logout_request:
            self._sign_logout_request(logout_request)
        return base64.b64encode(etree.tostring(logout_request)).decode()

    def encode_redirect(self) -> str:
        """Encode LogoutRequest for Redirect binding"""
        logout_request = self.build()
        # Note: For redirect binding, signatures are added as query parameters, not in XML
        # Ensure proper XML serialization with encoding declaration
        xml_str = etree.tostring(logout_request, encoding="UTF-8", xml_declaration=True)
        return deflate_and_base64_encode(xml_str.decode("UTF-8"))

    def get_redirect_url(self) -> str:
        """Build complete logout URL for redirect binding with signature if needed"""
        encoded_request = self.encode_redirect()
        params = {
            "SAMLRequest": encoded_request,
        }

        if self.relay_state:
            params["RelayState"] = self.relay_state

        if self.provider.signing_kp and self.provider.sign_logout_request:
            sig_alg = self.provider.signature_algorithm
            params["SigAlg"] = sig_alg

            # Build the string to sign
            query_string = self._build_signable_query_string(params)

            signature = self._sign_query_string(query_string)
            params["Signature"] = base64.b64encode(signature).decode()

        # Some SP's use query params on their sls endpoint
        separator = "&" if "?" in self.destination else "?"
        return f"{self.destination}{separator}{urlencode(params)}"

    def get_post_form_data(self) -> dict:
        """Get form data for POST binding"""
        return {
            "SAMLRequest": self.encode_post(),
            "RelayState": self.relay_state or "",
        }

    def _sign_logout_request(self, logout_request: _Element):
        """Sign the LogoutRequest element"""
        signature_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
            self.provider.signature_algorithm, xmlsec.constants.TransformRsaSha1
        )
        signature = xmlsec.template.create(
            logout_request,
            xmlsec.constants.TransformExclC14N,
            signature_algorithm_transform,
            ns=xmlsec.constants.DSigNs,
        )

        issuer = logout_request.find(f"{{{NS_SAML_ASSERTION}}}Issuer")
        if issuer is not None:
            issuer.addnext(signature)
        else:
            logout_request.insert(0, signature)

        self._sign(logout_request)

    def _sign(self, element: _Element):
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
        ctx.sign(remove_xml_newlines(element, signature_node))

    def _build_signable_query_string(self, params: dict) -> str:
        """Build query string for signing (order matters per SAML spec)"""
        # SAML spec requires specific order: SAMLRequest, RelayState, SigAlg
        # Values must be URL-encoded individually before concatenation
        ordered = []
        if "SAMLRequest" in params:
            ordered.append(f"SAMLRequest={quote(params['SAMLRequest'], safe='')}")
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
