"""Signing code goes here."""
from logging import getLogger

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from defusedxml import ElementTree
from signxml import XMLSigner
from signxml.util import strip_pem_header

from passbook.core.models import Setting
from passbook.lib.utils import render_to_string

LOGGER = getLogger(__name__)


def load_certificate(strip=False):
    """Get Public key from config"""
    cert = Setting.get('certificate')
    if strip:
        return strip_pem_header(cert.replace('\r', '')).replace('\n', '')
    return cert


def load_private_key():
    """Get Private Key from config"""
    return Setting.get('private_key')


def sign_with_signxml(private_key, data, cert, reference_uri=None):
    """Sign Data with signxml"""
    key = serialization.load_pem_private_key(
        str.encode('\n'.join([x.strip() for x in private_key.split('\n')])),
        password=None, backend=default_backend())
    root = ElementTree.fromstring(data)
    signer = XMLSigner(c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#')
    return ElementTree.tostring(signer.sign(root, key=key, cert=cert, reference_uri=reference_uri))


def get_signature_xml():
    """Returns XML Signature for subject."""
    return render_to_string('saml/xml/signature.xml', {})
