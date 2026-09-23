"""Create self-signed certificates"""

import datetime
import uuid

from cryptography import x509
from cryptography.exceptions import InternalError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.mldsa import (
    MLDSA44PrivateKey,
    MLDSA65PrivateKey,
    MLDSA87PrivateKey,
)
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.x509.oid import NameOID
from django.db import models
from django.utils.translation import gettext_lazy as _

from authentik import authentik_version
from authentik.crypto.models import CertificateKeyPair

# Key types whose signature scheme takes no separate hash algorithm (EdDSA, ML-DSA) and whose
# private keys can only be serialized as PKCS#8.
PKCS8_ONLY_KEY_TYPES = (
    Ed25519PrivateKey,
    Ed448PrivateKey,
    MLDSA44PrivateKey,
    MLDSA65PrivateKey,
    MLDSA87PrivateKey,
)


class KeyAlgorithmUnavailableError(ValueError):
    """The selected key algorithm cannot be generated in the current OpenSSL configuration,
    for example ML-DSA under a FIPS provider that predates it."""


class PrivateKeyAlg(models.TextChoices):
    """Algorithm to create private key with"""

    RSA = "rsa", _("rsa")
    ECDSA = "ecdsa", _("ecdsa")
    ED25519 = "ed25519", _("Ed25519")
    ED448 = "ed448", _("Ed448")
    MLDSA44 = "mldsa44", _("ML-DSA-44")
    MLDSA65 = "mldsa65", _("ML-DSA-65")
    MLDSA87 = "mldsa87", _("ML-DSA-87")


class CertificateBuilder:
    """Build self-signed certificates"""

    common_name: str
    alg: PrivateKeyAlg

    def __init__(self, name: str):
        self.alg = PrivateKeyAlg.RSA
        self.__public_key = None
        self.__private_key = None
        self.__builder = None
        self.__certificate = None
        self.common_name = name
        self.cert = CertificateKeyPair()

    def save(self) -> CertificateKeyPair:
        """Save generated certificate as model"""
        if not self.__certificate:
            raise ValueError("Certificated hasn't been built yet")
        self.cert.name = self.common_name
        self.cert.certificate_data = self.certificate
        self.cert.key_data = self.private_key
        self.cert.save()
        return self.cert

    def generate_private_key(self) -> PrivateKeyTypes:
        """Generate private key"""
        if self.alg == PrivateKeyAlg.ECDSA:
            return ec.generate_private_key(curve=ec.SECP256R1())
        if self.alg == PrivateKeyAlg.RSA:
            return rsa.generate_private_key(
                public_exponent=65537, key_size=4096, backend=default_backend()
            )
        if self.alg == PrivateKeyAlg.ED25519:
            return Ed25519PrivateKey.generate()
        if self.alg == PrivateKeyAlg.ED448:
            return Ed448PrivateKey.generate()
        if self.alg in (PrivateKeyAlg.MLDSA44, PrivateKeyAlg.MLDSA65, PrivateKeyAlg.MLDSA87):
            return self.generate_mldsa_private_key()
        raise ValueError(f"Invalid alg: {self.alg}")

    def generate_mldsa_private_key(self) -> PrivateKeyTypes:
        """Generate an ML-DSA (FIPS 204) private key.

        The validated OpenSSL FIPS provider authentik ships (3.1.2) predates ML-DSA, so with
        FIPS mode enabled OpenSSL cannot find an implementation and cryptography surfaces that as
        an opaque InternalError. Translate it into something an admin can act on."""
        key_classes = {
            PrivateKeyAlg.MLDSA44: MLDSA44PrivateKey,
            PrivateKeyAlg.MLDSA65: MLDSA65PrivateKey,
            PrivateKeyAlg.MLDSA87: MLDSA87PrivateKey,
        }
        try:
            return key_classes[self.alg].generate()
        except InternalError as exc:
            raise KeyAlgorithmUnavailableError(self.alg) from exc

    def build(
        self,
        validity_days: int = 365,
        subject_alt_names: list[str] | None = None,
    ):
        """Build self-signed certificate"""
        one_day = datetime.timedelta(1, 0, 0)
        self.__private_key = self.generate_private_key()
        self.__public_key = self.__private_key.public_key()
        alt_names: list[x509.GeneralName] = []
        for alt_name in subject_alt_names or []:
            if alt_name.strip() != "":
                alt_names.append(x509.DNSName(alt_name))
        self.__builder = (
            x509.CertificateBuilder()
            .subject_name(
                x509.Name(
                    [
                        x509.NameAttribute(NameOID.COMMON_NAME, self.common_name[:64]),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "authentik"),
                        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Self-signed"),
                    ]
                )
            )
            .issuer_name(
                x509.Name(
                    [
                        x509.NameAttribute(NameOID.COMMON_NAME, f"authentik {authentik_version()}"),
                    ]
                )
            )
            .not_valid_before(datetime.datetime.today() - one_day)
            .not_valid_after(datetime.datetime.today() + datetime.timedelta(days=validity_days))
            .serial_number(int(uuid.uuid4()))
            .public_key(self.__public_key)
        )
        if alt_names:
            self.__builder = self.__builder.add_extension(
                x509.SubjectAlternativeName(alt_names), critical=True
            )
        algo = hashes.SHA256()
        # EdDSA and ML-DSA don't take a hash algorithm
        if isinstance(self.__private_key, PKCS8_ONLY_KEY_TYPES):
            algo = None
        self.__certificate = self.__builder.sign(
            private_key=self.__private_key,
            algorithm=algo,
            backend=default_backend(),
        )

    @property
    def private_key(self):
        """Return private key in PEM format"""
        format = serialization.PrivateFormat.TraditionalOpenSSL
        if isinstance(self.__private_key, PKCS8_ONLY_KEY_TYPES):
            format = serialization.PrivateFormat.PKCS8
        return self.__private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=format,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

    @property
    def certificate(self):
        """Return certificate in PEM format"""
        return self.__certificate.public_bytes(
            encoding=serialization.Encoding.PEM,
        ).decode("utf-8")
