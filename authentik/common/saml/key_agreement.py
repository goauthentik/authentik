"""ECDH-ES key agreement for XML Encryption 1.1

RSA certificates receive the content encryption key through key transport (RSA-OAEP), which
libxmlsec handles. An EC key can't encrypt anything directly, so XML Encryption 1.1 defines key
agreement instead: the sender generates an ephemeral EC key, derives a shared secret with the
recipient's public key (ECDH-ES), runs that through a key derivation function (ConcatKDF) and
wraps the content encryption key with the result (AES Key Wrap).

This is implemented here rather than with libxmlsec, as key agreement is only supported by
libxmlsec 1.3 and newer, and isn't exposed by its Python bindings.

https://www.w3.org/TR/xmlenc-core1/#sec-ECDH-ES
"""

from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from os import urandom

from cryptography.exceptions import InvalidKey, UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from cryptography.hazmat.primitives.keywrap import (
    InvalidUnwrap,
    aes_key_unwrap,
    aes_key_wrap,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_der_public_key,
)
from cryptography.x509 import Certificate
from lxml.etree import Element, SubElement, _Element  # nosec

from authentik.common.saml.constants import (
    KW_AES128,
    KW_AES192,
    KW_AES256,
    NS_ENC,
    NS_SIGNATURE,
)
from authentik.sources.saml.exceptions import InvalidEncryption

NS_ENC11 = "http://www.w3.org/2009/xmlenc11#"
NS_SIGNATURE11 = "http://www.w3.org/2009/xmldsig11#"
NS_MAP = {"xenc": NS_ENC, "xenc11": NS_ENC11, "ds": NS_SIGNATURE, "dsig11": NS_SIGNATURE11}

ECDH_ES = "http://www.w3.org/2009/xmlenc11#ECDH-ES"
CONCAT_KDF = "http://www.w3.org/2009/xmlenc11#ConcatKDF"

# Key wrap algorithm to the size (in bytes) of the key encryption key it uses
KEY_WRAP_KEY_SIZES = {KW_AES128: 16, KW_AES192: 24, KW_AES256: 32}

DIGEST_SHA256 = "http://www.w3.org/2001/04/xmlenc#sha256"
DIGEST_SHA384 = "http://www.w3.org/2001/04/xmldsig-more#sha384"
DIGEST_SHA512 = "http://www.w3.org/2001/04/xmlenc#sha512"
KDF_DIGESTS: dict[str, type[hashes.HashAlgorithm]] = {
    DIGEST_SHA256: hashes.SHA256,
    DIGEST_SHA384: hashes.SHA384,
    DIGEST_SHA512: hashes.SHA512,
}

# Curves by the OID they're referenced with in a `dsig11:NamedCurve`
CURVES: dict[str, type[ec.EllipticCurve]] = {
    "urn:oid:1.2.840.10045.3.1.7": ec.SECP256R1,
    "urn:oid:1.3.132.0.34": ec.SECP384R1,
    "urn:oid:1.3.132.0.35": ec.SECP521R1,
}
CURVE_OIDS = {curve().name: oid for oid, curve in CURVES.items()}

# Empty bitstring. ConcatKDF parameters are hex-encoded bitstrings, prefixed with one octet that
# holds the number of padding bits
KDF_PARAM_EMPTY = "00"
# ConcatKDF's AlgorithmID identifies what the derived key is used for, which is to wrap the
# content encryption key. It has to be set, as some implementations (libxmlsec among them) refuse
# to derive a key without it.
KDF_ALGORITHM_ID = KW_AES256.encode()
KDF_PARAMS = ("AlgorithmID", "PartyUInfo", "PartyVInfo", "SuppPubInfo", "SuppPrivInfo")


def _kdf_param(params: _Element, name: str) -> bytes:
    """Decode a ConcatKDF parameter, which is a hex-encoded bitstring prefixed with the number
    of padding bits. Only whole octets are supported."""
    value = params.attrib.get(name)
    if value is None:
        return b""
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise InvalidEncryption(f"Invalid ConcatKDF parameter {name}.") from exc
    if not raw or raw[0] != 0:
        raise InvalidEncryption(f"Unsupported ConcatKDF parameter {name}.")
    return raw[1:]


def _derive(
    private_key: ec.EllipticCurvePrivateKey,
    public_key: ec.EllipticCurvePublicKey,
    digest: type[hashes.HashAlgorithm],
    length: int,
    other_info: bytes,
) -> bytes:
    """Derive the key encryption key from the ECDH shared secret"""
    shared_secret = private_key.exchange(ec.ECDH(), public_key)
    return ConcatKDFHash(algorithm=digest(), length=length, otherinfo=other_info).derive(
        shared_secret
    )


def build_encrypted_key(certificate: Certificate, key: bytes) -> _Element:
    """Wrap the content encryption key `key` for the EC public key of `certificate` and return
    it as an `xenc:EncryptedKey` element"""
    recipient_key = certificate.public_key()
    if not isinstance(recipient_key, ec.EllipticCurvePublicKey):
        raise InvalidEncryption("Key agreement requires an elliptic curve certificate.")
    curve_oid = CURVE_OIDS.get(recipient_key.curve.name)
    if curve_oid is None:
        raise InvalidEncryption(f"Unsupported curve {recipient_key.curve.name}.")

    ephemeral_key = ec.generate_private_key(recipient_key.curve)
    wrapped_key = aes_key_wrap(
        _derive(
            ephemeral_key,
            recipient_key,
            hashes.SHA256,
            KEY_WRAP_KEY_SIZES[KW_AES256],
            KDF_ALGORITHM_ID,
        ),
        key,
    )

    encrypted_key = Element(f"{{{NS_ENC}}}EncryptedKey", nsmap=NS_MAP)
    SubElement(encrypted_key, f"{{{NS_ENC}}}EncryptionMethod", Algorithm=KW_AES256)
    key_info = SubElement(encrypted_key, f"{{{NS_SIGNATURE}}}KeyInfo")
    agreement_method = SubElement(key_info, f"{{{NS_ENC}}}AgreementMethod", Algorithm=ECDH_ES)

    derivation_method = SubElement(
        agreement_method, f"{{{NS_ENC11}}}KeyDerivationMethod", Algorithm=CONCAT_KDF
    )
    kdf_params = SubElement(
        derivation_method,
        f"{{{NS_ENC11}}}ConcatKDFParams",
        AlgorithmID=f"00{KDF_ALGORITHM_ID.hex()}".upper(),
        PartyUInfo=KDF_PARAM_EMPTY,
        PartyVInfo=KDF_PARAM_EMPTY,
    )
    SubElement(kdf_params, f"{{{NS_SIGNATURE}}}DigestMethod", Algorithm=DIGEST_SHA256)

    originator = SubElement(agreement_method, f"{{{NS_ENC}}}OriginatorKeyInfo")
    ec_key_value = SubElement(
        SubElement(originator, f"{{{NS_SIGNATURE}}}KeyValue"), f"{{{NS_SIGNATURE11}}}ECKeyValue"
    )
    SubElement(ec_key_value, f"{{{NS_SIGNATURE11}}}NamedCurve", URI=curve_oid)
    SubElement(ec_key_value, f"{{{NS_SIGNATURE11}}}PublicKey").text = b64encode(
        ephemeral_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    ).decode()

    recipient = SubElement(agreement_method, f"{{{NS_ENC}}}RecipientKeyInfo")
    SubElement(
        SubElement(recipient, f"{{{NS_SIGNATURE}}}X509Data"), f"{{{NS_SIGNATURE}}}X509Certificate"
    ).text = b64encode(certificate.public_bytes(Encoding.DER)).decode()

    cipher_data = SubElement(encrypted_key, f"{{{NS_ENC}}}CipherData")
    SubElement(cipher_data, f"{{{NS_ENC}}}CipherValue").text = b64encode(wrapped_key).decode()
    return encrypted_key


def find_encrypted_key(parent: _Element) -> _Element | None:
    """Find an `xenc:EncryptedKey` below `parent` that uses ECDH-ES key agreement"""
    for encrypted_key in parent.iter(f"{{{NS_ENC}}}EncryptedKey"):
        agreement_method = encrypted_key.find(
            f"{{{NS_SIGNATURE}}}KeyInfo/{{{NS_ENC}}}AgreementMethod"
        )
        if agreement_method is not None and agreement_method.attrib.get("Algorithm") == ECDH_ES:
            return encrypted_key
    return None


def _originator_key(
    agreement_method: _Element, curve: ec.EllipticCurve
) -> ec.EllipticCurvePublicKey:
    """Load the sender's ephemeral public key, which has to be on the curve of our key"""
    originator = agreement_method.find(f"{{{NS_ENC}}}OriginatorKeyInfo")
    if originator is None:
        raise InvalidEncryption("Key agreement is missing the originator key.")
    try:
        der = originator.find(f".//{{{NS_SIGNATURE11}}}DEREncodedKeyValue")
        if der is not None:
            public_key = load_der_public_key(b64decode(der.text or "", validate=False))
        else:
            named_curve = originator.find(f".//{{{NS_SIGNATURE11}}}NamedCurve")
            point = originator.find(f".//{{{NS_SIGNATURE11}}}PublicKey")
            if named_curve is None or point is None:
                raise InvalidEncryption("Key agreement is missing the originator key.")
            named = CURVES.get(named_curve.attrib.get("URI", ""))
            if named is None:
                raise InvalidEncryption("Unsupported originator key curve.")
            public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                named(), b64decode(point.text or "", validate=False)
            )
    except (ValueError, BinasciiError, UnsupportedAlgorithm) as exc:
        raise InvalidEncryption("Invalid originator key.") from exc
    if not isinstance(public_key, ec.EllipticCurvePublicKey) or public_key.curve.name != curve.name:
        raise InvalidEncryption("Originator key does not match the curve of the decryption key.")
    return public_key


def unwrap_encrypted_key(encrypted_key: _Element, private_key: object) -> bytes:
    """Recover the content encryption key from an `xenc:EncryptedKey` that was wrapped using
    ECDH-ES key agreement with the public key of `private_key`"""
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise InvalidEncryption("Key agreement requires an elliptic curve decryption key.")
    method = encrypted_key.find(f"{{{NS_ENC}}}EncryptionMethod")
    key_size = KEY_WRAP_KEY_SIZES.get(
        method.attrib.get("Algorithm", "") if method is not None else ""
    )
    if key_size is None:
        raise InvalidEncryption("Unsupported key wrap algorithm.")

    agreement_method = encrypted_key.find(f"{{{NS_SIGNATURE}}}KeyInfo/{{{NS_ENC}}}AgreementMethod")
    if agreement_method is None or agreement_method.attrib.get("Algorithm") != ECDH_ES:
        raise InvalidEncryption("Unsupported key agreement algorithm.")
    derivation_method = agreement_method.find(f"{{{NS_ENC11}}}KeyDerivationMethod")
    if derivation_method is None or derivation_method.attrib.get("Algorithm") != CONCAT_KDF:
        raise InvalidEncryption("Unsupported key derivation algorithm.")
    kdf_params = derivation_method.find(f"{{{NS_ENC11}}}ConcatKDFParams")
    if kdf_params is None:
        raise InvalidEncryption("Key derivation is missing its parameters.")
    digest_method = kdf_params.find(f"{{{NS_SIGNATURE}}}DigestMethod")
    digest = KDF_DIGESTS.get(
        digest_method.attrib.get("Algorithm", "") if digest_method is not None else ""
    )
    if digest is None:
        raise InvalidEncryption("Unsupported key derivation digest.")
    other_info = b"".join(_kdf_param(kdf_params, name) for name in KDF_PARAMS)

    cipher_value = encrypted_key.find(f"{{{NS_ENC}}}CipherData/{{{NS_ENC}}}CipherValue")
    if cipher_value is None or not cipher_value.text:
        raise InvalidEncryption("Encrypted key is missing its value.")
    try:
        wrapped_key = b64decode(cipher_value.text, validate=False)
        key_encryption_key = _derive(
            private_key,
            _originator_key(agreement_method, private_key.curve),
            digest,
            key_size,
            other_info,
        )
        return aes_key_unwrap(key_encryption_key, wrapped_key)
    except (ValueError, BinasciiError, InvalidKey, InvalidUnwrap) as exc:
        raise InvalidEncryption("Failed to unwrap the encrypted key.") from exc


def generate_content_encryption_key(bits: int) -> bytes:
    """Generate a random content encryption key"""
    return urandom(bits // 8)
