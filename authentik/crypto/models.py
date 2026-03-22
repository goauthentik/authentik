"""authentik crypto models"""

from base64 import urlsafe_b64encode  # noqa: I001
from binascii import hexlify
from dataclasses import dataclass
from hashlib import md5, sha512
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
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
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


def generate_key_id(key_data: str) -> str:
    """Generate Key ID using SHA512 + urlsafe_b64encode."""
    if not key_data:
        return ""
    return urlsafe_b64encode(sha512(key_data.encode("utf-8")).digest()).decode("utf-8").rstrip("=")


def generate_key_id_legacy(key_data: str) -> str:
    """Generate Key ID using MD5 (legacy format for backwards compatibility)."""
    if not key_data:
        return ""
    return md5(key_data.encode("utf-8"), usedforsecurity=False).hexdigest()  # nosec


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
    kid = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text=_("Key ID generated from private key"),
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

    def ensure_fingerprint_fields(self, *, save: bool = True) -> None:
        """Populate fingerprint/cache fields if missing."""
        changed = False
        try:
            cert = load_pem_x509_certificate(
                self.certificate_data.encode("utf-8"), default_backend()
            )
        except Exception as exc:  # noqa
            # keep existing behavior: validation happens elsewhere
            return

        if not self.fingerprint_sha256:
            self.fingerprint_sha256 = fingerprint_sha256(cert)
            changed = True

        if changed and save:
            self.save(update_fields=["fingerprint_sha256"])

    def __str__(self) -> str:
        return f"Certificate-Key Pair {self.name}"

    class Meta:
        verbose_name = _("Certificate-Key Pair")
        verbose_name_plural = _("Certificate-Key Pairs")
        permissions = [
            ("view_certificatekeypair_certificate", _("View Certificate-Key pair's certificate")),
            ("view_certificatekeypair_key", _("View Certificate-Key pair's private key")),
        ]


@dataclass(frozen=True, slots=True)
class KeyPairRef:
    keypair: CertificateKeyPair
    order: int


class CertificateKeyPairRing(SerializerModel, ManagedModel, CreatedUpdatedModel):
    ring_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.TextField(blank=True, default="")

    keypairs = models.ManyToManyField(
        "CertificateKeyPair",
        through="CertificateKeyPairRingBinding",
        related_name="rings",
        blank=True,
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.crypto.api import CertificateKeyPairRingSerializer

        return CertificateKeyPairRingSerializer

    def ordered_bindings(self):
        return self.bindings.select_related("keypair").order_by("order", "keypair__kp_uuid")

    def ordered_keypairs(self):
        return [b.keypair for b in self.ordered_bindings()]

    @transaction.atomic
    def sync_membership(self, items: list[tuple[int, str]]) -> None:
        """Replace membership with provided ordered PEM cert list."""
        norm_in = [(int(o), (pem or "").strip()) for (o, pem) in items]
        norm_in.sort(key=lambda x: x[0])

        prev: int | None = None
        seen_fp: set[str] = set()
        resolved: list[KeyPairRef] = []

        for o, pem in norm_in:
            if o < 0:
                raise ValidationError("order must be >= 0")
            if prev is not None and o == prev:
                raise ValidationError(f"duplicate order={o}")
            prev = o
            if not pem:
                raise ValidationError("certificate_pem must be non-empty")

            try:
                cert = load_pem_x509_certificate(pem.encode("utf-8"), default_backend())
            except Exception as exc:  # noqa: BLE001
                raise ValidationError("invalid certificate_pem (cannot parse)") from exc

            fp = fingerprint_sha256(cert)
            if fp in seen_fp:
                raise ValidationError("duplicate certificate in membership (same fingerprint)")
            seen_fp.add(fp)

            kp = CertificateKeyPair.objects.filter(fingerprint_sha256=fp).first()
            if kp is None:
                kp = CertificateKeyPair.objects.create(
                    name=f"Imported {fp} ({uuid4()})",
                    certificate_data=pem,
                    key_data="",
                    fingerprint_sha256=fp,
                )
            elif not (kp.fingerprint_sha256 or "").strip():
                kp.fingerprint_sha256 = fp
                kp.save(update_fields=["fingerprint_sha256"])

            resolved.append(KeyPairRef(keypair=kp, order=o))

        self.sync_bindings(resolved)

    @transaction.atomic
    def sync_bindings(self, items: list[KeyPairRef]) -> None:
        """Replace membership with provided ordered keypair list."""
        norm = [(int(it.order), it.keypair) for it in items]
        norm.sort(key=lambda x: x[0])

        prev: int | None = None
        seen_kp: set[str] = set()
        for o, kp in norm:
            if o < 0:
                raise ValidationError("order must be >= 0")
            if prev is not None and o == prev:
                raise ValidationError(f"duplicate order={o}")
            prev = o
            kpid = str(kp.pk)
            if kpid in seen_kp:
                raise ValidationError("duplicate keypair in bindings")
            seen_kp.add(kpid)

        existing = list(
            self.bindings.select_related("keypair")
            .order_by("order", "keypair__kp_uuid")
            .values_list("order", "keypair__kp_uuid")
        )
        incoming = [(o, kp.pk) for (o, kp) in norm]
        if existing == incoming:
            return

        self.bindings.all().delete()
        CertificateKeyPairRingBinding.objects.bulk_create(
            [CertificateKeyPairRingBinding(ring=self, keypair=kp, order=o) for (o, kp) in norm]
        )

    class Meta:
        verbose_name = _("Certificate-Key Pair Ring")
        verbose_name_plural = _("Certificate-Key Pair Rings")


class CertificateKeyPairRingBinding(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    ring = models.ForeignKey(
        CertificateKeyPairRing,
        on_delete=models.CASCADE,
        related_name="bindings",
    )
    keypair = models.ForeignKey("CertificateKeyPair", on_delete=models.CASCADE)
    order = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = [("ring", "keypair")]
        indexes = [models.Index(fields=["ring", "order"])]
        indexes = [models.Index(fields=["ring", "order"])]

    def __str__(self) -> str:
        return f"KeyPairRingBinding({self.ring_id} -> {self.keypair_id}, order:{self.order})"
