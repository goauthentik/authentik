"""Shared SAML XML helpers"""

import base64
from collections.abc import Iterator
from typing import cast

from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import Certificate
from lxml.etree import _Element


def get_element_text(element: _Element) -> str:
    """Return the full text content of an XML element.

    ``Element.text`` only returns the text up to the first child node, so a value
    containing an XML comment (for example ``admin<!--x-->_user``) is silently
    truncated to ``admin``. Comment-excluding signature canonicalization
    (``xml-exc-c14n``) strips those comments before the digest is computed, so a
    signed value can be truncated after signing while keeping the signature valid.
    Reading the text via ``itertext()`` keeps the value equal to what was signed.
    """
    return "".join(cast(Iterator[str], element.itertext()))


def x509_certificate_b64(cert: Certificate) -> str:
    """Encode a single certificate as base64 DER, the format used by ds:X509Certificate.

    Encoding the parsed certificate rather than stripping the PEM headers off the stored
    text ensures that a certificate chain (e.g. certbot's fullchain.pem) only results in
    the leaf certificate being included, instead of the concatenated base64 of all
    certificates in the chain, which is not a valid certificate."""
    return base64.b64encode(cert.public_bytes(Encoding.DER)).decode()
