"""Create self-signed certificates"""
import datetime
import uuid
from typing import Optional

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from authentik import __version__
from authentik.crypto.models import CertificateKeyPair


class CertificateBuilder:
    """Build self-signed certificates"""

    common_name: str

    def __init__(self):
        self.__public_key = None
        self.__private_key = None
        self.__builder = None
        self.__certificate = None
        self.common_name = "authentik Self-signed Certificate"
        self.cert = CertificateKeyPair()

    def save(self) -> Optional[CertificateKeyPair]:
        """Save generated certificate as model"""
        if not self.__certificate:
            raise ValueError("Certificated hasn't been built yet")
        self.cert.name = self.common_name
        self.cert.certificate_data = self.certificate
        self.cert.key_data = self.private_key
        self.cert.save()
        return self.cert

    def build(
        self,
        validity_days: int = 365,
        subject_alt_names: Optional[list[str]] = None,
    ):
        """Build self-signed certificate"""
        one_day = datetime.timedelta(1, 0, 0)
        self.__private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=4096, backend=default_backend()
        )
        self.__public_key = self.__private_key.public_key()
        alt_names: list[x509.GeneralName] = [x509.DNSName(x) for x in subject_alt_names or []]
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
            .add_extension(x509.SubjectAlternativeName(alt_names), critical=True)
            .not_valid_before(datetime.datetime.today() - one_day)
            .not_valid_after(datetime.datetime.today() + datetime.timedelta(days=validity_days))
            .serial_number(int(uuid.uuid4()))
            .public_key(self.__public_key)
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
