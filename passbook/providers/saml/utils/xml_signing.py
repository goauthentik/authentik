"""Signing code goes here."""
from typing import TYPE_CHECKING

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from lxml import etree  # nosec
from signxml import XMLSigner, XMLVerifier
from structlog import get_logger

from passbook.lib.utils.template import render_to_string

if TYPE_CHECKING:
    from passbook.providers.saml.models import SAMLProvider

LOGGER = get_logger()


def sign_with_signxml(data: str, provider: "SAMLProvider", reference_uri=None) -> str:
    """Sign Data with signxml"""
    key = serialization.load_pem_private_key(
        str.encode("\n".join([x.strip() for x in provider.signing_key.split("\n")])),
        password=None,
        backend=default_backend(),
    )
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
        key=key,
        cert=[provider.signing_kp.certificate_data],
        reference_uri=reference_uri,
    )
    XMLVerifier().verify(signed, x509_cert=provider.signing_kp.certificate_data)
    return etree.tostring(signed).decode("utf-8")  # nosec


def get_signature_xml() -> str:
    """Returns XML Signature for subject."""
    return render_to_string("saml/xml/signature.xml", {})
