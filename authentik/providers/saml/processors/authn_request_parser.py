"""SAML AuthNRequest Parser and dataclass"""
from base64 import b64decode
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus
from xml.etree.ElementTree import ParseError  # nosec

import xmlsec
from defusedxml import ElementTree
from structlog.stdlib import get_logger

from authentik.lib.xml import lxml_from_string
from authentik.providers.saml.exceptions import CannotHandleAssertion
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.utils.encoding import decode_base64_and_inflate
from authentik.sources.saml.processors.constants import (
    DSA_SHA1,
    NS_MAP,
    NS_SAML_PROTOCOL,
    RSA_SHA1,
    RSA_SHA256,
    RSA_SHA384,
    RSA_SHA512,
    SAML_NAME_ID_FORMAT_UNSPECIFIED,
)

ERROR_CANNOT_DECODE_REQUEST = "Cannot decode SAML request."
ERROR_SIGNATURE_REQUIRED_BUT_ABSENT = (
    "Verification Certificate configured, but request is not signed."
)
ERROR_FAILED_TO_VERIFY = "Failed to verify signature"


@dataclass(slots=True)
class AuthNRequest:
    """AuthNRequest Dataclass"""

    id: Optional[str] = None

    relay_state: Optional[str] = None

    name_id_policy: str = SAML_NAME_ID_FORMAT_UNSPECIFIED


class AuthNRequestParser:
    """AuthNRequest Parser"""

    provider: SAMLProvider

    def __init__(self, provider: SAMLProvider):
        self.provider = provider
        self.logger = get_logger().bind(provider=self.provider)

    def _parse_xml(self, decoded_xml: str | bytes, relay_state: Optional[str]) -> AuthNRequest:
        root = ElementTree.fromstring(decoded_xml)

        # http://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf
        # `AssertionConsumerServiceURL` can be omitted, and we should fallback to the
        # default ACS URL
        if "AssertionConsumerServiceURL" not in root.attrib:
            request_acs_url = self.provider.acs_url.lower()
        else:
            request_acs_url = root.attrib["AssertionConsumerServiceURL"]

        if self.provider.acs_url.lower() != request_acs_url.lower():
            msg = (
                f"ACS URL of {request_acs_url} doesn't match Provider "
                f"ACS URL of {self.provider.acs_url}."
            )
            self.logger.warning(msg)
            raise CannotHandleAssertion(msg)

        auth_n_request = AuthNRequest(id=root.attrib["ID"], relay_state=relay_state)

        # Check if AuthnRequest has a NameID Policy object
        name_id_policies = root.findall(f"{{{NS_SAML_PROTOCOL}}}NameIDPolicy")
        if len(name_id_policies) > 0:
            name_id_policy = name_id_policies[0]
            auth_n_request.name_id_policy = name_id_policy.attrib.get(
                "Format", SAML_NAME_ID_FORMAT_UNSPECIFIED
            )

        return auth_n_request

    def parse(self, saml_request: str, relay_state: Optional[str] = None) -> AuthNRequest:
        """Validate and parse raw request with enveloped signautre."""
        try:
            decoded_xml = b64decode(saml_request.encode())
        except UnicodeDecodeError:
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST)

        verifier = self.provider.verification_kp
        if not verifier:
            return self._parse_xml(decoded_xml, relay_state)

        root = lxml_from_string(decoded_xml)
        xmlsec.tree.add_ids(root, ["ID"])
        signature_nodes = root.xpath("/samlp:AuthnRequest/ds:Signature", namespaces=NS_MAP)
        # No signatures, no verifier configured -> decode xml directly
        if len(signature_nodes) < 1:
            raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

        signature_node = signature_nodes[0]

        if signature_node is not None:
            try:
                ctx = xmlsec.SignatureContext()
                key = xmlsec.Key.from_memory(
                    verifier.certificate_data,
                    xmlsec.constants.KeyDataFormatCertPem,
                    None,
                )
                ctx.key = key
                ctx.verify(signature_node)
            except xmlsec.Error as exc:
                raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY) from exc

        return self._parse_xml(decoded_xml, relay_state)

    def parse_detached(
        self,
        saml_request: str,
        relay_state: Optional[str],
        signature: Optional[str] = None,
        sig_alg: Optional[str] = None,
    ) -> AuthNRequest:
        """Validate and parse raw request with detached signature"""
        try:
            decoded_xml = decode_base64_and_inflate(saml_request)
        except UnicodeDecodeError:
            raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST)

        verifier = self.provider.verification_kp
        if not verifier:
            return self._parse_xml(decoded_xml, relay_state)

        if verifier and not (signature and sig_alg):
            raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

        if signature and sig_alg:
            querystring = f"SAMLRequest={quote_plus(saml_request)}&"
            if relay_state is not None:
                querystring += f"RelayState={quote_plus(relay_state)}&"
            querystring += f"SigAlg={quote_plus(sig_alg)}"

            dsig_ctx = xmlsec.SignatureContext()
            key = xmlsec.Key.from_memory(
                verifier.certificate_data, xmlsec.constants.KeyDataFormatCertPem, None
            )
            dsig_ctx.key = key

            sign_algorithm_transform_map = {
                DSA_SHA1: xmlsec.constants.TransformDsaSha1,
                RSA_SHA1: xmlsec.constants.TransformRsaSha1,
                RSA_SHA256: xmlsec.constants.TransformRsaSha256,
                RSA_SHA384: xmlsec.constants.TransformRsaSha384,
                RSA_SHA512: xmlsec.constants.TransformRsaSha512,
            }
            sign_algorithm_transform = sign_algorithm_transform_map.get(
                sig_alg, xmlsec.constants.TransformRsaSha1
            )

            try:
                dsig_ctx.verify_binary(
                    querystring.encode("utf-8"),
                    sign_algorithm_transform,
                    b64decode(signature),
                )
            except xmlsec.Error as exc:
                raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY) from exc
        try:
            return self._parse_xml(decoded_xml, relay_state)
        except ParseError as exc:
            raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY) from exc

    def idp_initiated(self) -> AuthNRequest:
        """Create IdP Initiated AuthNRequest"""
        relay_state = None
        if self.provider.default_relay_state != "":
            relay_state = self.provider.default_relay_state
        return AuthNRequest(relay_state=relay_state)
