"""passbook crypto models"""
from binascii import hexlify
from typing import Optional
from uuid import uuid4

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import Certificate, load_pem_x509_certificate
from django.db import models
from django.utils.translation import gettext_lazy as _

from passbook.lib.models import CreatedUpdatedModel


class CertificateKeyPair(CreatedUpdatedModel):
    """CertificateKeyPair that can be used for signing or encrypting if `key_data`
    is set, otherwise it can be used to verify remote data."""

    kp_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField()
    certificate_data = models.TextField(help_text=_("PEM-encoded Certificate data"))
    key_data = models.TextField(
        help_text=_(
            "Optional Private Key. If this is set, you can use this keypair for encryption."
        ),
        blank=True,
        default="",
    )

    _cert: Optional[Certificate] = None
    _key: Optional[RSAPrivateKey] = None

    @property
    def certificate(self) -> Certificate:
        """Get python cryptography Certificate instance"""
        if not self._cert:
            self._cert = load_pem_x509_certificate(
                self.certificate_data.encode("utf-8"), default_backend()
            )
        return self._cert

    @property
    def private_key(self) -> Optional[RSAPrivateKey]:
        """Get python cryptography PrivateKey instance"""
        if not self._key:
            self._key = load_pem_private_key(
                str.encode("\n".join([x.strip() for x in self.key_data.split("\n")])),
                password=None,
                backend=default_backend(),
            )
        return self._key

    @property
    def fingerprint(self) -> str:
        """Get SHA256 Fingerprint of certificate_data"""
        return hexlify(self.certificate.fingerprint(hashes.SHA256()), ":").decode(
            "utf-8"
        )

    def __str__(self) -> str:
        return f"Certificate-Key Pair {self.name} {self.fingerprint}"

    class Meta:

        verbose_name = _("Certificate-Key Pair")
        verbose_name_plural = _("Certificate-Key Pairs")
