"""Shared SAML signature verification utilities"""

from base64 import b64decode
from urllib.parse import quote_plus

import xmlsec

from authentik.common.saml.constants import (
    NS_MAP,
    SIGN_ALGORITHM_TRANSFORM_MAP,
)
from authentik.common.saml.exceptions import CannotHandleAssertion
from authentik.lib.xml import lxml_from_string

ERROR_SIGNATURE_REQUIRED_BUT_ABSENT = (
    "Verification Certificate configured, but message is not signed."
)
ERROR_FAILED_TO_VERIFY = "Failed to verify signature"


def verify_enveloped_signature(raw_xml: bytes, verification_kp, xpath: str):
    """Verify an enveloped XML signature.

    Args:
        raw_xml: The raw XML bytes
        verification_kp: CertificateKeyPair with certificate_data
        xpath: XPath to signature node, e.g. '/samlp:LogoutRequest/ds:Signature'
    """
    root = lxml_from_string(raw_xml)
    xmlsec.tree.add_ids(root, ["ID"])
    signature_nodes = root.xpath(xpath, namespaces=NS_MAP)

    if len(signature_nodes) < 1:
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

    signature_node = signature_nodes[0]

    try:
        ctx = xmlsec.SignatureContext()
        key = xmlsec.Key.from_memory(
            verification_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
            None,
        )
        ctx.key = key
        ctx.verify(signature_node)
    except xmlsec.Error as exc:
        raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY) from exc


def verify_detached_signature(
    saml_param_name: str,
    saml_value: str,
    relay_state: str | None,
    signature: str | None,
    sig_alg: str | None,
    verification_kp,
):
    """Verify a detached redirect-binding signature.

    Args:
        saml_param_name: "SAMLRequest" or "SAMLResponse"
        saml_value: The raw base64+deflated SAML message value
        relay_state: RelayState value, if present
        signature: Base64-encoded signature from query params
        sig_alg: Signature algorithm URI from query params
        verification_kp: CertificateKeyPair with certificate_data
    """
    if not (signature and sig_alg):
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

    querystring = f"{saml_param_name}={quote_plus(saml_value)}&"
    if relay_state is not None:
        querystring += f"RelayState={quote_plus(relay_state)}&"
    querystring += f"SigAlg={quote_plus(sig_alg)}"

    dsig_ctx = xmlsec.SignatureContext()
    key = xmlsec.Key.from_memory(
        verification_kp.certificate_data, xmlsec.constants.KeyDataFormatCertPem, None
    )
    dsig_ctx.key = key

    sign_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
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
