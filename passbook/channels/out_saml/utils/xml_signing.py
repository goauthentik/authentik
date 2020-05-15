"""Signing code goes here."""
from typing import TYPE_CHECKING

from lxml import etree  # nosec
from signxml import XMLSigner, XMLVerifier
from structlog import get_logger

from passbook.lib.utils.template import render_to_string

if TYPE_CHECKING:
    from passbook.channels.out_saml.models import SAMLOutlet

LOGGER = get_logger()


def sign_with_signxml(data: str, provider: "SAMLOutlet", reference_uri=None) -> str:
    """Sign Data with signxml"""
    # defused XML is not used here because it messes up XML namespaces
    # Data is trusted, so lxml is ok
    root = etree.fromstring(data)  # nosec
    signer = XMLSigner(
        c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
        signature_algorithm=provider.signature_algorithm,
        digest_algorithm=provider.digest_algorithm,
    )
    signed = signer.sign(
        root,
        key=provider.signing_kp.private_key,
        cert=[provider.signing_kp.certificate_data],
        reference_uri=reference_uri,
    )
    XMLVerifier().verify(signed, x509_cert=provider.signing_kp.certificate_data)
    return etree.tostring(signed).decode("utf-8")  # nosec


def get_signature_xml() -> str:
    """Returns XML Signature for subject."""
    return render_to_string("saml/xml/signature.xml", {})
