"""SAML AuthNRequest Parser and dataclass"""
from base64 import b64decode
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from defusedxml import ElementTree
from signxml import XMLVerifier
from structlog import get_logger

from passbook.providers.saml.exceptions import CannotHandleAssertion
from passbook.providers.saml.models import SAMLProvider
from passbook.providers.saml.utils.encoding import decode_base64_and_inflate
from passbook.sources.saml.processors.constants import (
    NS_SAML_PROTOCOL,
    SAML_NAME_ID_FORMAT_EMAIL,
)

LOGGER = get_logger()


@dataclass
class AuthNRequest:
    """AuthNRequest Dataclass"""

    # pylint: disable=invalid-name
    id: Optional[str] = None

    relay_state: Optional[str] = None

    name_id_policy: str = SAML_NAME_ID_FORMAT_EMAIL


class AuthNRequestParser:
    """AuthNRequest Parser"""

    provider: SAMLProvider

    def __init__(self, provider: SAMLProvider):
        self.provider = provider

    def _parse_xml(self, decoded_xml: str, relay_state: Optional[str]) -> AuthNRequest:
        root = ElementTree.fromstring(decoded_xml)

        request_acs_url = root.attrib["AssertionConsumerServiceURL"]

        if self.provider.acs_url.lower() != request_acs_url.lower():
            msg = (
                f"ACS URL of {request_acs_url} doesn't match Provider "
                f"ACS URL of {self.provider.acs_url}."
            )
            LOGGER.info(msg)
            raise CannotHandleAssertion(msg)

        auth_n_request = AuthNRequest(id=root.attrib["ID"], relay_state=relay_state)

        # Check if AuthnRequest has a NameID Policy object
        name_id_policies = root.findall(f"{{{NS_SAML_PROTOCOL}}}:NameIDPolicy")
        if len(name_id_policies) > 0:
            name_id_policy = name_id_policies[0]
            auth_n_request.name_id_policy = name_id_policy.attrib["Format"]

        return auth_n_request

    def parse(self, saml_request: str, relay_state: Optional[str]) -> AuthNRequest:
        """Validate and parse raw request with enveloped signautre."""
        decoded_xml = decode_base64_and_inflate(saml_request)

        if self.provider.verification_kp:
            try:
                XMLVerifier().verify(
                    decoded_xml,
                    x509_cert=self.provider.verification_kp.certificate_data,
                )
            except InvalidSignature as exc:
                raise CannotHandleAssertion("Failed to verify signature") from exc

        return self._parse_xml(decoded_xml, relay_state)

    def parse_detached(
        self,
        saml_request: str,
        relay_state: Optional[str],
        signature: Optional[str] = None,
        sig_alg: Optional[str] = None,
    ) -> AuthNRequest:
        """Validate and parse raw request with detached signature"""
        decoded_xml = decode_base64_and_inflate(saml_request)

        if signature and sig_alg:
            # if sig_alg == "http://www.w3.org/2000/09/xmldsig#rsa-sha1":
            sig_hash = hashes.SHA1()  # nosec

            querystring = f"SAMLRequest={quote_plus(saml_request)}&"
            if relay_state is not None:
                querystring += f"RelayState={quote_plus(relay_state)}&"
            querystring += f"SigAlg={sig_alg}"

            if not self.provider.verification_kp:
                raise CannotHandleAssertion(
                    "Provider does not have a Validation Certificate configured."
                )
            public_key = self.provider.verification_kp.private_key.public_key()
            try:
                public_key.verify(
                    b64decode(signature),
                    querystring.encode(),
                    padding.PSS(
                        mgf=padding.MGF1(sig_hash), salt_length=padding.PSS.MAX_LENGTH
                    ),
                    sig_hash,
                )
            except InvalidSignature as exc:
                raise CannotHandleAssertion("Failed to verify signature") from exc
        return self._parse_xml(decoded_xml, relay_state)

    def idp_initiated(self) -> AuthNRequest:
        """Create IdP Initiated AuthNRequest"""
        return AuthNRequest()
