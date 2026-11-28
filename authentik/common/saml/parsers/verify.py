"""Shared SAML signature verification"""

from base64 import b64decode
from collections.abc import Sequence
from urllib.parse import urlencode

import xmlsec
from lxml.etree import _Element  # nosec

from authentik.common.saml.constants import NS_MAP, SIGN_ALGORITHM_TRANSFORM_MAP
from authentik.common.saml.exceptions import (
    ERROR_CANNOT_DECODE_REQUEST,
    ERROR_FAILED_TO_VERIFY,
    ERROR_SIGNATURE_REQUIRED_BUT_ABSENT,
    CannotHandleAssertion,
)
from authentik.lib.xml import UnsafeXML, lxml_from_string


def verify_enveloped_signature(raw_xml: bytes, certificates: Sequence[str], xpath: str) -> None:
    """Verify an enveloped XML signature (POST binding).

    The signature is accepted when it verifies with any of the PEM `certificates`, so a peer can
    roll over its key. `xpath` selects the signature node, for example
    `/samlp:LogoutRequest/ds:Signature`."""
    try:
        root = lxml_from_string(raw_xml)
    except UnsafeXML as exc:
        raise CannotHandleAssertion(ERROR_CANNOT_DECODE_REQUEST, detail=exc) from exc
    xmlsec.tree.add_ids(root, ["ID"])
    signature_nodes = root.xpath(xpath, namespaces=NS_MAP)
    if not isinstance(signature_nodes, list) or len(signature_nodes) < 1:
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)
    signature_node = signature_nodes[0]
    if not isinstance(signature_node, _Element):
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

    last_exc: xmlsec.Error | None = None
    for certificate in certificates:
        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(certificate, xmlsec.constants.KeyDataFormatCertPem, None)
        try:
            ctx.verify(signature_node)
        except xmlsec.Error as exc:
            last_exc = exc
            continue
        return
    raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY, detail=last_exc) from last_exc


def verify_detached_signature(  # noqa: PLR0913
    saml_param_name: str,
    saml_value: str,
    relay_state: str | None,
    signature: str | None,
    sig_alg: str | None,
    certificates: Sequence[str],
) -> None:
    """Verify a detached signature (Redirect binding).

    The signature is accepted when it verifies with any of the PEM `certificates`.
    `saml_param_name` is either `SAMLRequest` or `SAMLResponse`, and `saml_value` the
    encoded message as it was received."""
    if not (signature and sig_alg):
        raise CannotHandleAssertion(ERROR_SIGNATURE_REQUIRED_BUT_ABSENT)

    params = {saml_param_name: saml_value}
    if relay_state is not None:
        params["RelayState"] = relay_state
    params["SigAlg"] = sig_alg
    querystring = urlencode(params)

    sign_algorithm_transform = SIGN_ALGORITHM_TRANSFORM_MAP.get(
        sig_alg, xmlsec.constants.TransformRsaSha1
    )

    last_exc: xmlsec.Error | None = None
    for certificate in certificates:
        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(certificate, xmlsec.constants.KeyDataFormatCertPem, None)
        try:
            ctx.verify_binary(
                querystring.encode("utf-8"),
                sign_algorithm_transform,
                b64decode(signature),
            )
        except xmlsec.Error as exc:
            last_exc = exc
            continue
        return
    raise CannotHandleAssertion(ERROR_FAILED_TO_VERIFY, detail=last_exc) from last_exc
