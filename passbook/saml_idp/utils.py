"""Wrappers to de/encode and de/inflate strings"""
import base64
import datetime
import uuid
import zlib

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def decode_base64_and_inflate(b64string):
    """Base64 decode and ZLib decompress b64string"""
    decoded_data = base64.b64decode(b64string)
    return zlib.decompress(decoded_data, -15)


def deflate_and_base64_encode(string_val):
    """Base64 and ZLib Compress b64string"""
    zlibbed_str = zlib.compress(string_val)
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string)


def nice64(src):
    """ Returns src base64-encoded and formatted nicely for our XML. """
    return base64.b64encode(src).decode('utf-8').replace('\n', '')


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
        one_day = datetime.timedelta(1, 0, 0)
        self.__private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.__public_key = self.__private_key.public_key()
        self.__builder = \
            x509.CertificateBuilder(). \
            subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, u'passbook Self-signed SAML Certificate'),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'passbook'),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'Self-signed'),
            ])). \
            issuer_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, u'passbook Self-signed SAML Certificate'),
            ])). \
            not_valid_before(datetime.datetime.today() - one_day). \
            not_valid_after(datetime.datetime.today() + datetime.timedelta(days=365)). \
            serial_number(int(uuid.uuid4())). \
            public_key(self.__public_key)
        self.__certificate = self.__builder.sign(
            private_key=self.__private_key, algorithm=hashes.SHA256(),
            backend=default_backend()
        )

    @property
    def private_key(self):
        """Return private key in PEM format"""
        return self.__private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode('utf-8')

    @property
    def certificate(self):
        """Return certificate in PEM format"""
        return self.__certificate.public_bytes(
            encoding=serialization.Encoding.PEM,
        ).decode('utf-8')
