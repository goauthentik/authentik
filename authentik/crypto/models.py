"""authentik crypto models"""

from binascii import hexlify
from hashlib import md5
from ssl import PEM_FOOTER, PEM_HEADER
from textwrap import wrap
from uuid import uuid4

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.dsa import DSAPublicKey
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import Certificate, load_pem_x509_certificate
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.blueprints.models import ManagedModel
from authentik.lib.models import CreatedUpdatedModel, SerializerModel

LOGGER = get_logger()


def format_cert(raw_pam: str) -> str:
    """Format a PEM certificate that is either missing its header/footer or is in a single line"""
    return "\n".join([PEM_HEADER, *wrap(raw_pam.replace("\n", ""), 64), PEM_FOOTER])


class KeyType(models.TextChoices):
    """Cryptographic key algorithm types"""

    RSA = "rsa", _("RSA")
    EC = "ec", _("Elliptic Curve")
    DSA = "dsa", _("DSA")
    ED25519 = "ed25519", _("Ed25519")
    ED448 = "ed448", _("Ed448")


def fingerprint_sha256(cert: Certificate) -> str:
    """Get SHA256 Fingerprint of certificate"""
    return hexlify(cert.fingerprint(hashes.SHA256()), ":").decode("utf-8")


def detect_key_type(certificate: Certificate) -> str | None:
    """Detect the key algorithm type by parsing the certificate's public key"""
    try:
        public_key = certificate.public_key()
        if isinstance(public_key, RSAPublicKey):
            return KeyType.RSA
        if isinstance(public_key, EllipticCurvePublicKey):
            return KeyType.EC
        if isinstance(public_key, DSAPublicKey):
            return KeyType.DSA
        if isinstance(public_key, Ed25519PublicKey):
            return KeyType.ED25519
        if isinstance(public_key, Ed448PublicKey):
            return KeyType.ED448
    except (ValueError, TypeError, AttributeError) as exc:
        LOGGER.warning("Failed to detect key type", exc=exc)
    return None


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
    key_type = models.CharField(
        max_length=16,
        choices=KeyType.choices,
        null=True,
        blank=True,
        help_text=_("Key algorithm type detected from the certificate's public key"),
    )
    cert_expiry = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Certificate expiry date"),
    )
    cert_subject = models.TextField(
        null=True,
        blank=True,
        help_text=_("Certificate subject as RFC4514 string"),
    )
    fingerprint_sha256 = models.CharField(
        max_length=95,
        null=True,
        blank=True,
        help_text=_("SHA256 fingerprint of the certificate"),
    )
    fingerprint_sha1 = models.CharField(
        max_length=59,
        null=True,
        blank=True,
        help_text=_("SHA1 fingerprint of the certificate"),
    )

    _cert: Certificate | None = None
    _private_key: PrivateKeyTypes | None = None
    _public_key: PublicKeyTypes | None = None

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
    def public_key(self) -> PublicKeyTypes | None:
        """Get public key of the private key"""
        if not self._public_key:
            self._public_key = self.private_key.public_key()
        return self._public_key

    @property
    def private_key(
        self,
    ) -> PrivateKeyTypes | None:
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
    def kid(self):
        """Get Key ID used for JWKS"""
        return (
            md5(self.key_data.encode("utf-8"), usedforsecurity=False).hexdigest()
            if self.key_data
            else ""
        )  # nosec

    def __str__(self) -> str:
        return f"Certificate-Key Pair {self.name}"

    class Meta:
        verbose_name = _("Certificate-Key Pair")
        verbose_name_plural = _("Certificate-Key Pairs")
        permissions = [
            ("view_certificatekeypair_certificate", _("View Certificate-Key pair's certificate")),
            ("view_certificatekeypair_key", _("View Certificate-Key pair's private key")),
        ]
