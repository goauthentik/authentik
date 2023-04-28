"""authentik crypto models"""
from binascii import hexlify
from hashlib import md5
from typing import Optional
from uuid import uuid4

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.types import PRIVATE_KEY_TYPES, PUBLIC_KEY_TYPES
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import Certificate, load_pem_x509_certificate
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.blueprints.models import ManagedModel
from authentik.lib.models import CreatedUpdatedModel, SerializerModel

LOGGER = get_logger()


class CertificateKeyPair(SerializerModel, ManagedModel, CreatedUpdatedModel):
    """CertificateKeyPair that can be used for signing or encrypting if `key_data`
    is set, otherwise it can be used to verify remote data."""

    kp_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    name = models.TextField(unique=True)
    certificate_data = models.TextField(help_text=_("PEM-encoded Certificate data"))
    key_data = models.TextField(
        help_text=_(
            "Optional Private Key. If this is set, you can use this keypair for encryption."
        ),
        blank=True,
        default="",
    )

    _cert: Optional[Certificate] = None
    _private_key: Optional[PRIVATE_KEY_TYPES] = None
    _public_key: Optional[PUBLIC_KEY_TYPES] = None

    @property
    def serializer(self) -> Serializer:
        from authentik.crypto.api import CertificateKeyPairSerializer

        return CertificateKeyPairSerializer

    @property
    def certificate(self) -> Certificate:
        """Get python cryptography Certificate instance"""
        if not self._cert:
            self._cert = load_pem_x509_certificate(
                self.certificate_data.encode("utf-8"), default_backend()
            )
        return self._cert

    @property
    def public_key(self) -> Optional[PUBLIC_KEY_TYPES]:
        """Get public key of the private key"""
        if not self._public_key:
            self._public_key = self.private_key.public_key()
        return self._public_key

    @property
    def private_key(
        self,
    ) -> Optional[PRIVATE_KEY_TYPES]:
        """Get python cryptography PrivateKey instance"""
        if not self._private_key and self.key_data != "":
            try:
                self._private_key = load_pem_private_key(
                    str.encode("\n".join([x.strip() for x in self.key_data.split("\n")])),
                    password=None,
                    backend=default_backend(),
                )
            except ValueError as exc:
                LOGGER.warning(exc)
                return None
        return self._private_key

    @property
    def fingerprint_sha256(self) -> str:
        """Get SHA256 Fingerprint of certificate_data"""
        return hexlify(self.certificate.fingerprint(hashes.SHA256()), ":").decode("utf-8")

    @property
    def fingerprint_sha1(self) -> str:
        """Get SHA1 Fingerprint of certificate_data"""
        return hexlify(self.certificate.fingerprint(hashes.SHA1()), ":").decode("utf-8")  # nosec

    @property
    def kid(self):
        """Get Key ID used for JWKS"""
        return md5(self.key_data.encode("utf-8")).hexdigest() if self.key_data else ""  # nosec

    def __str__(self) -> str:
        return f"Certificate-Key Pair {self.name}"

    class Meta:
        verbose_name = _("Certificate-Key Pair")
        verbose_name_plural = _("Certificate-Key Pairs")
