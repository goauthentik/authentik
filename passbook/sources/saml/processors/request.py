"""SAML AuthnRequest Processor"""
from base64 import b64encode
from typing import Dict
from urllib.parse import quote_plus

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.http import HttpRequest
from lxml import etree  # nosec
from lxml.etree import Element  # nosec
from signxml import XMLSigner

from passbook.providers.saml.utils import get_random_id
from passbook.providers.saml.utils.encoding import deflate_and_base64_encode
from passbook.providers.saml.utils.time import get_time_string
from passbook.sources.saml.models import SAMLSource
from passbook.sources.saml.processors.constants import (
    NS_MAP,
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
)

SESSION_REQUEST_ID = "passbook_source_saml_request_id"


class RequestProcessor:
    """SAML AuthnRequest Processor"""

    source: SAMLSource
    http_request: HttpRequest

    relay_state: str

    request_id: str
    issue_instant: str

    def __init__(self, source: SAMLSource, request: HttpRequest, relay_state: str):
        self.source = source
        self.http_request = request
        self.relay_state = relay_state
        self.request_id = get_random_id()
        self.http_request.session[SESSION_REQUEST_ID] = self.request_id
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
        Signature. See https://docs.oasis-open.org/security/saml/v2.0/saml-bindings-2.0-os.pdf"""
        auth_n_request = self.get_auth_n()

        saml_request = deflate_and_base64_encode(
            etree.tostring(auth_n_request).decode()
        )

        response_dict = {
            "SAMLRequest": saml_request,
        }

        if self.relay_state != "":
            response_dict["RelayState"] = self.relay_state

        if self.source.signing_kp:
            sig_alg = "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
            sig_hash = hashes.SHA1()  # nosec
            # Create the full querystring in the correct order to be signed
            querystring = f"SAMLRequest={quote_plus(saml_request)}&"
            if self.relay_state != "":
                querystring += f"RelayState={quote_plus(self.relay_state)}&"
            querystring += f"SigAlg={sig_alg}"

            signature = self.source.signing_kp.private_key.sign(
                querystring.encode(),
                padding.PSS(
                    mgf=padding.MGF1(sig_hash), salt_length=padding.PSS.MAX_LENGTH
                ),
                sig_hash,
            )
            response_dict["SigAlg"] = sig_alg
            response_dict["Signature"] = b64encode(signature).decode()

        return response_dict
