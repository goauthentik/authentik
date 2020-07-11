"""SAML AuthnRequest Processor"""
from typing import Dict

from django.http import HttpRequest
from lxml import etree  # nosec
from lxml.etree import Element  # nosec
from signxml import XMLSigner, methods

from passbook.providers.saml.utils import get_random_id
from passbook.providers.saml.utils.encoding import deflate_and_base64_encode
from passbook.providers.saml.utils.time import get_time_string
from passbook.sources.saml.models import SAMLSource
from passbook.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    NS_SIGNATURE,
)


class RequestProcessor:
    """SAML AuthnRequest Processor"""

    source: SAMLSource
    http_request: HttpRequest

    request_id: str
    issue_instant: str

    def __init__(self, source: SAMLSource, request: HttpRequest):
        self.source = source
        self.http_request = request
        self.request_id = get_random_id()
        self.issue_instant = get_time_string()

    def get_issuer(self) -> Element:
        """Get Issuer Element"""
        issuer = Element(f"{{{NS_SAML_ASSERTION}}}Issuer")
        issuer.text = self.source.get_issuer(self.http_request)
        return issuer

    def get_name_id_policy(self) -> Element:
        """Get NameID Policy Element"""
        name_id_policy = Element(f"{{{NS_SAML_PROTOCOL}}}NameIDPolicy")
        name_id_policy.text = self.source.name_id_policy
        return name_id_policy

    def get_auth_n(self) -> Element:
        """Get full AuthnRequest"""
        auth_n_request = Element(f"{{{NS_SAML_PROTOCOL}}}AuthnRequest", nsmap=NS_MAP)
        auth_n_request.attrib[
            "AssertionConsumerServiceURL"
        ] = self.source.build_full_url(self.http_request)
        auth_n_request.attrib["Destination"] = self.source.sso_url
        auth_n_request.attrib["ID"] = self.request_id
        auth_n_request.attrib["IssueInstant"] = self.issue_instant
        auth_n_request.attrib["ProtocolBinding"] = self.source.binding_type
        auth_n_request.attrib["Version"] = "2.0"
        # Create issuer object
        auth_n_request.append(self.get_issuer())
        # Create NameID Policy Object
        auth_n_request.append(self.get_name_id_policy())
        return auth_n_request

    def build_auth_n(self) -> str:
        """Get Signed string representation of AuthN Request
        (used for POST Bindings)"""
        auth_n_request = self.get_auth_n()

        if self.source.signing_kp:
            signed_request = XMLSigner().sign(
                auth_n_request,
                cert=self.source.signing_kp.certificate_data,
                key=self.source.signing_kp.key_data,
            )
            return etree.tostring(signed_request).decode()

        return etree.tostring(auth_n_request).decode()

    def build_auth_n_detached(self) -> Dict[str, str]:
        """Get Dict AuthN Request for Redirect bindings, with detached
        Signature"""
        auth_n_request = self.get_auth_n()

        response_dict = {
            "SAMLRequest": deflate_and_base64_encode(
                etree.tostring(auth_n_request).decode()
            ),
        }

        if self.source.signing_kp:
            signer = XMLSigner(methods.detached)
            signature = signer.sign(
                auth_n_request,
                cert=self.source.signing_kp.certificate_data,
                key=self.source.signing_kp.key_data,
            )
            signature_value = signature.find(
                f".//{{{NS_SIGNATURE}}}SignatureValue"
            ).text
            response_dict["Signature"] = signature_value
            response_dict["SigAlg"] = signer.sign_alg

        return response_dict
