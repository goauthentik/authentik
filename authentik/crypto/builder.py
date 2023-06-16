"""Create self-signed certificates"""
import datetime
import uuid
from typing import Optional

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.x509.oid import NameOID

from authentik import __version__
from authentik.crypto.models import CertificateKeyPair


class CertificateBuilder:
    """Build self-signed certificates"""

    common_name: str

    _use_ec_private_key: bool

    def __init__(self, name: str, use_ec_private_key=False):
        self._use_ec_private_key = use_ec_private_key
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
        if self._use_ec_private_key:
            return ec.generate_private_key(curve=ec.SECP256R1)
        return rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )

    def build(
        self,
        validity_days: int = 365,
        subject_alt_names: Optional[list[str]] = None,
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
                        x509.NameAttribute(NameOID.COMMON_NAME, self.common_name),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "authentik"),
                        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Self-signed"),
                    ]
                )
            )
            .issuer_name(
                x509.Name(
                    [
                        x509.NameAttribute(NameOID.COMMON_NAME, f"authentik {__version__}"),
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
        self.__certificate = self.__builder.sign(
            private_key=self.__private_key,
            algorithm=hashes.SHA256(),
            backend=default_backend(),
        )

    @property
    def private_key(self):
        """Return private key in PEM format"""
        return self.__private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

    @property
    def certificate(self):
        """Return certificate in PEM format"""
        return self.__certificate.public_bytes(
            encoding=serialization.Encoding.PEM,
        ).decode("utf-8")
