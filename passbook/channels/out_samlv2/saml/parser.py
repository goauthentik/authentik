"""SAML Request Parse/builder"""
from typing import TYPE_CHECKING, Optional

from defusedxml import ElementTree
from signxml import XMLVerifier

from passbook.channels.out_samlv2.saml.constants import (
    NS_SAML_ASSERTION,
    NS_SAML_PROTOCOL,
    SAML_ATTRIB_ACS_URL,
    SAML_ATTRIB_DESTINATION,
    SAML_ATTRIB_ID,
    SAML_ATTRIB_ISSUE_INSTANT,
    SAML_ATTRIB_PROTOCOL_BINDING,
)
from passbook.channels.out_samlv2.saml.utils import decode_base64_and_inflate
from passbook.crypto.models import CertificateKeyPair

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec


# pylint: disable=too-many-instance-attributes
class SAMLRequest:
    """SAML Request data class, parse raw base64-encoded data, checks signature and more"""

    _root: "Element"

    acs_url: str
    destination: str
    id: str
    issue_instant: str
    protocol_binding: str

    issuer: str

    is_signed: bool
    _detached_signature: str

    def __init__(self):
        self.acs_url = ""
        self.destination = ""
        # pylint: disable=invalid-name
        self.id = ""
        self.issue_instant = ""
        self.protocol_binding = ""

    @staticmethod
    def parse(raw: str, detached_signature: Optional[str] = None) -> "SAMLRequest":
        """Prase SAML request from raw string, which can be base64 encoded and deflated.
        Optionally accepts a detached_signature, as from a REDIRECT request."""
        decoded_xml = decode_base64_and_inflate(raw)
        root = ElementTree.fromstring(decoded_xml)
        req = SAMLRequest()
        req._root = root  # pylint: disable=protected-access
        # Verify the root element's tag
        _expected_tag = f"{{{NS_SAML_PROTOCOL}}}AuthnRequest"
        if root.tag != _expected_tag:
            raise ValueError(
                f"Invalid root tag, got '{root.tag}', expected '{_expected_tag}."
            )
        req.acs_url = root.attrib[SAML_ATTRIB_ACS_URL]
        req.destination = root.attrib[SAML_ATTRIB_DESTINATION]
        req.id = root.attrib[SAML_ATTRIB_ID]
        req.issue_instant = root.attrib[SAML_ATTRIB_ISSUE_INSTANT]
        req.protocol_binding = root.attrib[SAML_ATTRIB_PROTOCOL_BINDING]
        req.issuer = root.find(f"{{{NS_SAML_ASSERTION}}}Issuer").text
        # Check if this Request is signed
        if detached_signature:
            # pylint: disable=protected-access
            req._detached_signature = detached_signature
        return req

    def verify_signature(self, keypair: CertificateKeyPair):
        """Verify signature of SAML Request.
        Raises `cryptography.exceptions.InvalidSignature` on validaton failure."""
        verifier = XMLVerifier()
        if self._detached_signature:
            verifier.verify(
                self._detached_signature, x509_cert=keypair.certificate_data
            )
        else:
            verifier.verify(self._root, x509_cert=keypair.certificate_data)
