"""Shared SAML signature verification"""

from base64 import b64decode
from urllib.parse import urlencode

import xmlsec
from lxml.etree import _Element  # nosec

from authentik.common.saml.constants import NS_MAP, SIGN_ALGORITHM_TRANSFORM_MAP
from authentik.common.saml.exceptions import (
    ERROR_FAILED_TO_VERIFY,
    ERROR_SIGNATURE_REQUIRED_BUT_ABSENT,
    CannotHandleAssertion,
)
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.xml import UnsafeXML, lxml_from_string


def verify_enveloped_signature(
    raw_xml: bytes, verification_kp: CertificateKeyPair, xpath: str
) -> None:
    """Verify an enveloped XML signature (POST binding).

    `xpath` selects the signature node, for example `/samlp:LogoutRequest/ds:Signature`."""
    try:
        root = lxml_from_string(raw_xml)
    except UnsafeXML as exc:
        raise CannotHandleAssertion(str(exc)) from exc
    xmlsec.tree.add_ids(root, ["ID"])
    signature_nodes = root.xpath(xpath, namespaces=NS_MAP)
    if not isinstance(signature_nodes, list) or len(signature_nodes) < 1:
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)
    signature_node = signature_nodes[0]
    if not isinstance(signature_node, _Element):
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

    try:
        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(
            verification_kp.certificate_data,
            xmlsec.constants.KeyDataFormatCertPem,
            None,
        )
        ctx.verify(signature_node)
    except xmlsec.Error as exc:
        raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY) from exc


def verify_detached_signature(  # noqa: PLR0913
    saml_param_name: str,
    saml_value: str,
    relay_state: str | None,
    signature: str | None,
    sig_alg: str | None,
    verification_kp: CertificateKeyPair,
) -> None:
    """Verify a detached signature (Redirect binding).

    `saml_param_name` is either `SAMLRequest` or `SAMLResponse`, and `saml_value` the
    encoded message as it was received."""
    if not (signature and sig_alg):
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

    params = {saml_param_name: saml_value}
    if relay_state is not None:
        params["RelayState"] = relay_state
    params["SigAlg"] = sig_alg
    querystring = urlencode(params)

    ctx = xmlsec.SignatureContext()
    ctx.key = xmlsec.Key.from_memory(
        verification_kp.certificate_data, xmlsec.constants.KeyDataFormatCertPem, None
    )
    sign_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
        sig_alg, xmlsec.constants.TransformRsaSha1
    )

    try:
        ctx.verify_binary(
            querystring.encode("utf-8"),
            sign_algorithm_transform,
            b64decode(signature),
        )
    except xmlsec.Error as exc:
        raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY) from exc
