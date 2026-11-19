"""Shared XMLDSIG signing for SAML responses, logout, and metadata."""

import xmlsec
from lxml.etree import _Element  # nosec

from authentik.common.saml.constants import DIGEST_ALGORITHM_TRANSLATION_MAP
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.xml import remove_xml_newlines
from authentik.providers.saml.models import SAMLProvider


def sign_xml_element(
    element: _Element,
    provider: SAMLProvider,
    *,
    id_attribute: str = "ID",
) -> None:
    """Sign `element` using the enveloped signature node already attached to it."""
    signing_kp: CertificateKeyPair | None = provider.signing_kp
    if signing_kp is None:
        raise ValueError("Cannot sign without a signing keypair.")
    digest_algorithm_transform = DIGEST_ALGORITHM_TRANSLATION_MAP.get(
        provider.digest_algorithm, xmlsec.constants.TransformSha1
    )
    xmlsec.tree.add_ids(element, [id_attribute])
    signature_node = xmlsec.tree.find_node(element, xmlsec.constants.NodeSignature)
    reference = xmlsec.template.add_reference(
        signature_node,
        digest_algorithm_transform,
        uri="#" + element.attrib[id_attribute],
    )
    xmlsec.template.add_transform(reference, xmlsec.constants.TransformEnveloped)
    xmlsec.template.add_transform(reference, xmlsec.constants.TransformExclC14N)
    key_info = xmlsec.template.ensure_key_info(signature_node)
    xmlsec.template.add_x509_data(key_info)

    context = xmlsec.SignatureContext()
    key = xmlsec.Key.from_memory(
        signing_kp.key_data,
        xmlsec.constants.KeyDataFormatPem,
        None,
    )
    key.load_cert_from_memory(
        signing_kp.certificate_data,
        xmlsec.constants.KeyDataFormatCertPem,
    )
    context.key = key
    context.sign(remove_xml_newlines(element, signature_node))
