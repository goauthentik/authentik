"""SAML AuthNRequest Parser and dataclass"""
from typing import Optional
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from defusedxml import ElementTree
from signxml import XMLVerifier
from structlog import get_logger

from passbook.providers.saml.exceptions import CannotHandleAssertion
from passbook.providers.saml.models import SAMLProvider
from passbook.providers.saml.utils import get_random_id
from passbook.providers.saml.utils.encoding import decode_base64_and_inflate

LOGGER = get_logger()


@dataclass
class AuthNRequest:
    """AuthNRequest Dataclass"""

    # pylint: disable=invalid-name
    id: Optional[str] = None

    relay_state: str = ""


class AuthNRequestParser:
    """AuthNRequest Parser"""

    provider: SAMLProvider

    def __init__(self, provider: SAMLProvider):
        self.provider = provider

    def parse(self, saml_request: str, relay_state: str) -> AuthNRequest:
        """Parses various parameters from _request_xml into _request_params."""

        decoded_xml = decode_base64_and_inflate(saml_request)

        if self.provider.require_signing and self.provider.signing_kp:
            try:
                XMLVerifier().verify(
                    decoded_xml, x509_cert=self.provider.signing_kp.certificate_data
                )
            except InvalidSignature as exc:
                raise CannotHandleAssertion("Failed to verify signature") from exc

        root = ElementTree.fromstring(decoded_xml)

        request_acs_url = root.attrib["AssertionConsumerServiceURL"]

        if self.provider.acs_url != request_acs_url:
            msg = (
                f"ACS URL of {request_acs_url} doesn't match Provider "
                f"ACS URL of {self.provider.acs_url}."
            )
            LOGGER.info(msg)
            raise CannotHandleAssertion(msg)

        auth_n_request = AuthNRequest(id=root.attrib["ID"], relay_state=relay_state)
        return auth_n_request

    def idp_initiated(self) -> AuthNRequest:
        """Create IdP Initiated AuthNRequest"""
        return AuthNRequest()
