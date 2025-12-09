"""authentik crypto signals"""

from binascii import hexlify
from datetime import datetime
from ssl import CertificateError

from cryptography.hazmat.primitives import hashes
from cryptography.x509 import Certificate
from django.db.models.signals import pre_save
from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.crypto.models import (
    CertificateKeyPair,
    detect_key_type,
    fingerprint_sha256,
    generate_key_id,
)

LOGGER = get_logger()


def extract_certificate_metadata(certificate: Certificate) -> dict[str, str | datetime]:
    """Extract all metadata fields from a certificate."""
    metadata = {}

    try:
        metadata["key_type"] = detect_key_type(certificate)
        metadata["cert_expiry"] = certificate.not_valid_after_utc
        metadata["cert_subject"] = certificate.subject.rfc4514_string()
        metadata["fingerprint_sha256"] = fingerprint_sha256(certificate)
        metadata["fingerprint_sha1"] = hexlify(
            certificate.fingerprint(hashes.SHA1()), ":"  # nosec
        ).decode("utf-8")
    except (ValueError, TypeError, AttributeError) as exc:
        raise CertificateError(f"Invalid certificate metadata: {exc}") from exc

    return metadata


@receiver(pre_save, sender="authentik_crypto.CertificateKeyPair")
def certificate_key_pair_pre_save(
    sender: type[CertificateKeyPair], instance: CertificateKeyPair, **_
):
    """Automatically populate certificate metadata fields before saving"""

    # Only extract metadata if certificate_data is present
    if not instance.certificate_data:
        return

    try:
        metadata = extract_certificate_metadata(instance.certificate)
    except (CertificateError, ValueError, TypeError, AttributeError) as exc:
        LOGGER.warning("Failed to extract certificate metadata", exc=exc)
        return

    instance.key_type = metadata["key_type"]
    instance.cert_expiry = metadata["cert_expiry"]
    instance.cert_subject = metadata["cert_subject"]
    instance.fingerprint_sha256 = metadata["fingerprint_sha256"]
    instance.fingerprint_sha1 = metadata["fingerprint_sha1"]

    # Generate kid only if not already set (preserves backfilled MD5 values)
    if not instance.kid and instance.key_data:
        instance.kid = generate_key_id(instance.key_data)
