"""authentik crypto signals"""

from binascii import hexlify

from cryptography.hazmat.primitives import hashes
from cryptography.x509 import Certificate
from django.db.models import Model
from django.db.models.signals import pre_save
from django.dispatch import receiver

from authentik.crypto.models import detect_key_type, fingerprint_sha256


def extract_certificate_metadata(certificate: Certificate) -> dict:
    """Extract all metadata fields from a certificate.

    Returns a dict with keys: key_type, cert_expiry, cert_subject,
    fingerprint_sha256, fingerprint_sha1. Values will be None if extraction fails.
    """
    metadata = {}

    # Detect key type
    try:
        metadata["key_type"] = detect_key_type(certificate)
    except (ValueError, TypeError, AttributeError):
        metadata["key_type"] = None

    # Get certificate expiry
    try:
        metadata["cert_expiry"] = certificate.not_valid_after_utc
    except (ValueError, TypeError, AttributeError):
        metadata["cert_expiry"] = None

    # Get certificate subject
    try:
        metadata["cert_subject"] = certificate.subject.rfc4514_string()
    except (ValueError, TypeError, AttributeError):
        metadata["cert_subject"] = None

    # Get SHA256 fingerprint
    try:
        metadata["fingerprint_sha256"] = fingerprint_sha256(certificate)
    except (ValueError, TypeError, AttributeError):
        metadata["fingerprint_sha256"] = None

    # Get SHA1 fingerprint
    try:
        metadata["fingerprint_sha1"] = hexlify(
            certificate.fingerprint(hashes.SHA1()), ":"  # nosec
        ).decode("utf-8")
    except (ValueError, TypeError, AttributeError):
        metadata["fingerprint_sha1"] = None

    return metadata


@receiver(pre_save, sender="authentik_crypto.CertificateKeyPair")
def certificate_key_pair_pre_save(sender: type[Model], instance, **_):
    """Automatically populate certificate metadata fields before saving"""
    from authentik.crypto.models import CertificateKeyPair

    if not isinstance(instance, CertificateKeyPair):
        return

    # Extract all metadata from the certificate
    metadata = extract_certificate_metadata(instance.certificate)

    # Update instance fields (only set key_type if not already set)
    if not instance.key_type:
        instance.key_type = metadata["key_type"]
    instance.cert_expiry = metadata["cert_expiry"]
    instance.cert_subject = metadata["cert_subject"]
    instance.fingerprint_sha256 = metadata["fingerprint_sha256"]
    instance.fingerprint_sha1 = metadata["fingerprint_sha1"]
