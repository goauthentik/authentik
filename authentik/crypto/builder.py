"""Create self-signed certificates"""
import datetime
import uuid

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


class CertificateBuilder:
    """Build self-signed certificates"""

    __public_key = None
    __private_key = None
    __builder = None
    __certificate = None

    def __init__(self):
        self.__public_key = None
        self.__private_key = None
        self.__builder = None
        self.__certificate = None

    def build(self):
        """Build self-signed certificate"""
        one_day = datetime.timedelta(1, 0, 0)
        self.__private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self.__public_key = self.__private_key.public_key()
        self.__builder = (
            x509.CertificateBuilder()
            .subject_name(
                x509.Name(
                    [
                        x509.NameAttribute(
                            NameOID.COMMON_NAME,
                            "authentik Self-signed Certificate",
                        ),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "authentik"),
                        x509.NameAttribute(
                            NameOID.ORGANIZATIONAL_UNIT_NAME, "Self-signed"
                        ),
                    ]
                )
            )
            .issuer_name(
                x509.Name(
                    [
                        x509.NameAttribute(
                            NameOID.COMMON_NAME,
                            "authentik Self-signed Certificate",
                        ),
                    ]
                )
            )
            .not_valid_before(datetime.datetime.today() - one_day)
            .not_valid_after(datetime.datetime.today() + datetime.timedelta(days=365))
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
