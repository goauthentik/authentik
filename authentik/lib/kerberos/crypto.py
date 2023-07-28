"""Kerberos cryptography primitives"""
import math

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from authentik.lib.kerberos import iana


def nfold(data: bytes, size: int) -> bytes:
    """
    Stretches data to be of length `size`. Size must be in bytes.

    See https://www.rfc-editor.org/rfc/rfc3961#section-5.1

    Original paper with implementation example: https://www.gnu.org/software/shishi/ides.pdf
    """

    def rot13(data: bytes, step: int) -> bytes:
        """
        Rotate `data` 13 bits right. Step is the number of times the rotation will be performed.
        """

        if step == 0:
            return data

        _data = int.from_bytes(data, byteorder="big")
        mod = (1 << (step * 8)) - 1

        if step == 1:
            shift = 5
        else:
            shift = 13
        result = ((_data >> shift) | (_data << (step * 8 - shift))) & mod
        return result.to_bytes(step, byteorder="big")

    def ones_complement_add(lhs: bytes, rhs: bytes) -> bytes:
        """
        One's complement addition (with end-around carry).
        """
        if len(lhs) != len(rhs):
            raise ValueError(
                "Cannot one's complement add two numbers of different size"
            )
        size = len(lhs)

        result = [left + right for left, right in zip(lhs, rhs)]
        while any(digit & ~0xFF for digit in result):
            result = [(result[i - size + 1] >> 8) + (result[i] & 0xFF) for i in range(size)]
        return bytes(result)

    # def ones_complement_add(add1: bytes, add2: bytes) -> bytes:
    #     """
    #     One's complement addition (without end-around carry).
    #     """
    #     if len(add1) != len(add2):
    #         raise KerberosCryptoValueError(
    #             "Cannot one's complement add two numbers of different size"
    #         )
    #     size = len(add1)
    #     mod = 1 << (size * 8)
    #     result = int.from_bytes(add1, byteorder="big") + int.from_bytes(add2, byteorder="big")
    #     return (
    #         result.to_bytes(size, byteorder="big")
    #         if result < mod
    #         else ((result + 1) % mod).to_bytes(size, byteorder="big")
    #     )

    data_size = len(data)
    lcm = math.lcm(size, data_size)

    buf = bytes()
    for _ in range(lcm // data_size):
        buf += data
        data = rot13(data, data_size)

    result = bytes([0] * size)
    for i in range(0, lcm, size):
        result = ones_complement_add(result, buf[i : i + size])

    return result


class EncryptionType:
    """Kerberos generic encryption type"""

    ENC_TYPE: iana.EncryptionType
    CHECKSUM_TYPE: iana.ChecksumType

    KEY_BYTES: int
    KEY_SEED_BITS: int

    HASH_ALGORITHM: hashes.HashAlgorithm

    DEFAULT_STRING_TO_KEY_PARAMS: str

    HMAC_BITS: int

    MESSAGE_BLOCK_BYTES: int
    CYPHER_BLOCK_BITS: int
    CONFOUNDER_BYTES: int

    @classmethod
    def random_to_key(cls, data: bytes) -> bytes:
        """
        Derive a protocol key from random data.
        """
        raise NotImplementedError

    @classmethod
    def derive_random(cls, key: bytes, usage: bytes) -> bytes:
        """
        Derive random data from a protocol key and a usage.
        """
        raise NotImplementedError

    @classmethod
    def derive_key(cls, key: bytes, usage: bytes) -> bytes:
        """
        Derive data from a protocol key and a usage.
        """
        raise NotImplementedError

    @classmethod
    def string_to_key(cls, password: bytes, salt: bytes, params: str | None = None) -> bytes:
        """
        Derive a protocol key from a password and a salt.
        """
        raise NotImplementedError

    @classmethod
    def encrypt_data(cls, key: bytes, data: bytes) -> bytes:
        """
        Encrypt data with a procotol key.
        """
        raise NotImplementedError

    @classmethod
    def encrypt_message(cls, key: bytes, message: bytes, usage: int) -> bytes:
        """
        Encrypt a message with a procotol key.
        """
        raise NotImplementedError

    @classmethod
    def decrypt_data(cls, key: bytes, data: bytes) -> bytes:
        """
        Decrypt data with a procotol key.
        """
        raise NotImplementedError

    @classmethod
    def decrypt_message(cls, key: bytes, ciphertext: bytes, usage: int) -> bytes:
        """
        Decrypt a message with a procotol key.
        """
        raise NotImplementedError

    @classmethod
    def verify_integrity(cls, key: bytes, ciphertext: bytes, usage: int) -> bool:
        """
        Verify ciphertext integrity with a protocol key.
        """
        raise NotImplementedError

    @classmethod
    def get_checksum_hash(cls, key: bytes, data: bytes, usage: int) -> bytes:
        """
        Compute data checksum hash with a procotol key.
        """
        raise NotImplementedError

    @classmethod
    def verify_checksum(cls, key: bytes, data: bytes, checksum: bytes, usage: int) -> bytes:
        """
        Verify a data checksum with a procotol key.
        """
        raise NotImplementedError


class Rfc3961(EncryptionType):
    """
    Encryption and checksumming method as defined in RFC 3961.

    We only implement methods that are re-used in Rfc3962, as that RFC depends
    on this one, and we're not implementing DES3 as that has been deprecated by
    RFC 8429.

    See https://www.rfc-editor.org/rfc/rfc3961
    """

    @classmethod
    def random_to_key(cls, data: bytes) -> bytes:
        """
        Derive a protocol key from random data as defined in RFC 3961.

        See https://www.rfc-editor.org/rfc/rfc3961#section-6.3.1
        """
        return data

    @classmethod
    def derive_random(cls, key: bytes, usage: bytes) -> bytes:
        """
        Derives random data from a protocol key and a usage as defined in RFC 3961.

        See https://www.rfc-editor.org/rfc/rfc3961#section-5.1
        """
        usage_folded = nfold(usage, cls.CYPHER_BLOCK_BITS // 8)
        data = cls.encrypt_data(key, usage_folded)
        result = bytes()
        while len(result) < cls.KEY_SEED_BITS // 8:
            result += data
            data = cls.encrypt_data(key, data)
        return result[: cls.KEY_SEED_BITS // 8]

    @classmethod
    def derive_key(cls, key: bytes, usage: bytes) -> bytes:
        """
        Derive data from a protocol key and a usage as defined in RFC 3961.

        See https://www.rfc-editor.org/rfc/rfc3961#section-5.1
        """
        return cls.random_to_key(cls.derive_random(key, usage))


class Rfc3962(Rfc3961):
    """
    Encryption and checksumming method as defined in RFC 3962.

    See https://www.rfc-editor.org/rfc/rfc3962
    """

    @classmethod
    def string_to_key(cls, password: bytes, salt: bytes, params: str | None = None) -> bytes:
        """
        Derive a protocol key from a password and a salt as defined in RFC 3962.

        See https://www.rfc-editor.org/rfc/rfc3962#section-4
        """
        if params is None:
            params = cls.DEFAULT_STRING_TO_KEY_PARAMS
        if len(params) != 8:
            raise ValueError("Invalid params length")
        iterations = int(params, base=16)

        kdf = PBKDF2HMAC(
            algorithm=cls.HASH_ALGORITHM(),
            length=cls.KEY_BYTES,
            salt=salt,
            iterations=iterations,
        )
        tmp_key = cls.random_to_key(kdf.derive(password))
        return cls.derive_key(tmp_key, "kerberos".encode())

    @classmethod
    def encrypt_data(cls, key: bytes, data: bytes) -> bytes:
        """
        Encrypt data with a procotol key as defined in RFC 3962.

        See https://www.rfc-editor.org/rfc/rfc3962#section-6
        """
        initialization_vector = bytes([0] * (cls.CYPHER_BLOCK_BITS // 8))
        cipher = Cipher(algorithms.AES(key), modes.CBC(initialization_vector))
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()


class Rfc8009(EncryptionType):
    """
    Encryption and checksumming methods as defined in RFC 8009.

    See https://www.rfc-editor.org/rfc/rfc8009
    """

    ENC_NAME: str

    @classmethod
    def random_to_key(cls, data: bytes) -> bytes:
        """
        Derive a protocol key from random data as defined in RFC 8009.

        See https://www.rfc-editor.org/rfc/rfc8009#section-5
        """
        return data

    @classmethod
    def _kdc_hmac_sha2(cls, key: bytes, label: bytes, context: bytes, size: int) -> bytes:
        """
        Defined in RFC 8009.
        Context is optional and can be `bytes()`.
        Size is in bits.
        """
        data = (
            0x00000001.to_bytes(4, byteorder="big")
            + label
            + 0x00.to_bytes(1, byteorder="big")
            + context
            + size.to_bytes(4, byteorder="big")
        )
        hasher = hmac.HMAC(key, cls.HASH_ALGORITHM())
        hasher.update(data)
        return hasher.finalize()[: size // 8]

    @classmethod
    def derive_random(cls, key: bytes, usage: bytes) -> bytes:
        """
        Derives random data from a protocol key and a usage as defined in RFC 8009.

        See https://www.rfc-editor.org/rfc/rfc8009#section-3
        """
        return cls._kdc_hmac_sha2(key, "prf".encode(), usage, cls.HASH_ALGORITHM.digest_size * 8)

    @classmethod
    def derive_key(cls, key: bytes, usage: bytes) -> bytes:
        """
        Derive data from a protocol key and a usage as defined in RFC 8009.

        See https://www.rfc-editor.org/rfc/rfc8009#section-5
        """
        if cls.ENC_TYPE == iana.EncryptionType.AES256_CTS_HMAC_SHA384_192 and (
            usage == "kerberos".encode() or usage[-1] == 0xAA
        ):
            size = 256
        else:
            size = cls.KEY_SEED_BITS
        return cls.random_to_key(cls._kdc_hmac_sha2(key, usage, bytes(), size))

    @classmethod
    def string_to_key(cls, password: bytes, salt: bytes, params: str | None = None) -> bytes:
        """
        Derive a protocol key from a password and a salt as defined in RFC 8009.

        See https://www.rfc-editor.org/rfc/rfc8009#section-4
        """
        if params is None:
            params = cls.DEFAULT_STRING_TO_KEY_PARAMS
        if len(params) != 8:
            raise ValueError("Invalid params length")
        iterations = int(params, base=16)

        salt = cls.ENC_NAME.encode() + bytes([0]) + salt

        if cls.ENC_TYPE == iana.EncryptionType.AES256_CTS_HMAC_SHA384_192:
            length = 32
        else:
            length = cls.KEY_BYTES

        kdf = PBKDF2HMAC(
            algorithm=cls.HASH_ALGORITHM(),
            length=length,
            salt=salt,
            iterations=iterations,
        )
        tmp_key = cls.random_to_key(kdf.derive(password))

        return cls.derive_key(tmp_key, "kerberos".encode())


class Aes128CtsHmacSha196(Rfc3962):
    """
    aes128-cts-hmac-sha1-96 encryption type as defined in RFC 3962.

    See https://www.rfc-editor.org/rfc/rfc3962#section-6
    """

    ENC_TYPE = iana.EncryptionType.AES128_CTS_HMAC_SHA1_96
    CHECKSUM_TYPE = iana.ChecksumType.HMAC_SHA1_96_AES128
    ENC_NAME = "aes128-cts-hmac-sha1-96"

    KEY_BYTES = algorithms.AES128.key_size // 8
    KEY_SEED_BITS = KEY_BYTES * 8

    HASH_ALGORITHM = hashes.SHA1

    DEFAULT_STRING_TO_KEY_PARAMS = "00001000"

    HMAC_BITS = 96

    MESSAGE_BLOCK_BYTES = 1
    CYPHER_BLOCK_BITS = algorithms.AES128.block_size
    CONFOUNDER_BYTES = CYPHER_BLOCK_BITS // 8


class Aes256CtsHmacSha196(Rfc3962):
    """
    aes256-cts-hmac-sha1-96 encryption type as defined in RFC 3962.

    See https://www.rfc-editor.org/rfc/rfc3962#section-6
    """

    ENC_TYPE = iana.EncryptionType.AES256_CTS_HMAC_SHA1_96
    CHECKSUM_TYPE = iana.ChecksumType.HMAC_SHA1_96_AES256
    ENC_NAME = "aes256-cts-hmac-sha1-96"

    KEY_BYTES = algorithms.AES256.key_size // 8
    KEY_SEED_BITS = KEY_BYTES * 8

    HASH_ALGORITHM = hashes.SHA1

    DEFAULT_STRING_TO_KEY_PARAMS = "00001000"

    HMAC_BITS = 96

    MESSAGE_BLOCK_BYTES = 1
    CYPHER_BLOCK_BITS = algorithms.AES256.block_size
    CONFOUNDER_BYTES = CYPHER_BLOCK_BITS // 8


class Aes128CtsHmacSha256128(Rfc8009):
    """
    aes128-cts-hmac-sha256-128 encryption type as defined in RFC 8009.

    See https://www.rfc-editor.org/rfc/rfc8009
    """

    ENC_TYPE = iana.EncryptionType.AES128_CTS_HMAC_SHA256_128
    CHECKSUM_TYPE = iana.ChecksumType.HMAC_SHA256_128_AES128
    ENC_NAME = "aes128-cts-hmac-sha256-128"

    KEY_BYTES = algorithms.AES128.key_size // 8
    KEY_SEED_BITS = KEY_BYTES * 8

    HASH_ALGORITHM = hashes.SHA256

    DEFAULT_STRING_TO_KEY_PARAMS = "00008000"

    HMAC_BITS = 128

    MESSAGE_BLOCK_BYTES = 1
    CYPHER_BLOCK_BITS = algorithms.AES128.block_size
    CONFOUNDER_BYTES = CYPHER_BLOCK_BITS // 8


class Aes256CtsHmacSha384192(Rfc8009):
    """
    aes256-cts-hmac-sha384-192 encryption type as defined in RFC 8009.

    See https://www.rfc-editor.org/rfc/rfc8009
    """

    ENC_TYPE = iana.EncryptionType.AES256_CTS_HMAC_SHA384_192
    CHECKSUM_TYPE = iana.ChecksumType.HMAC_SHA384_192_AES256
    ENC_NAME = "aes256-cts-hmac-sha384-192"

    KEY_BYTES = 192 // 8
    KEY_SEED_BITS = KEY_BYTES * 8

    HASH_ALGORITHM = hashes.SHA384

    DEFAULT_STRING_TO_KEY_PARAMS = "00008000"

    HMAC_BITS = 192

    MESSAGE_BLOCK_BYTES = 1
    CYPHER_BLOCK_BITS = algorithms.AES256.block_size
    CONFOUNDER_BYTES = CYPHER_BLOCK_BITS // 8


SUPPORTED_ENCTYPES = (
    Aes128CtsHmacSha196,
    Aes256CtsHmacSha196,
    Aes128CtsHmacSha256128,
    Aes256CtsHmacSha384192,
)

def get_enctype_from_value(value: int) -> EncryptionType:
    for enctype in SUPPORTED_ENCTYPES:
        if enctype.ENC_TYPE.value == value:
            return enctype
    raise IndexError("No matching enctype found")
