from base64 import urlsafe_b64encode
from json import dumps
from secrets import token_bytes

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from django.http import HttpResponse
from jwcrypto.common import base64url_decode, base64url_encode

from authentik.enterprise.providers.apple_psso.models import AppleDevice


def length_prefixed(data: bytes) -> bytes:
    length = len(data)
    return length.to_bytes(4, "big") + data


def build_apu(public_key: ec.EllipticCurvePublicKey):
    # X9.63 representation: 0x04 || X || Y
    public_numbers = public_key.public_numbers()

    x_bytes = public_numbers.x.to_bytes(32, "big")
    y_bytes = public_numbers.y.to_bytes(32, "big")

    x963 = bytes([0x04]) + x_bytes + y_bytes

    result = length_prefixed(b"APPLE") + length_prefixed(x963)

    return result


def encrypt_token_with_a256_gcm(body: dict, device_encryption_key: str, apv: bytes) -> str:
    ephemeral_key = ec.generate_private_key(curve=ec.SECP256R1())
    device_public_key = serialization.load_pem_public_key(
        device_encryption_key.encode(), backend=default_backend()
    )

    shared_secret_z = ephemeral_key.exchange(ec.ECDH(), device_public_key)

    apu = build_apu(ephemeral_key.public_key())

    jwe_header = {
        "enc": "A256GCM",
        "kid": "ephemeralKey",
        "epk": {
            "x": base64url_encode(
                ephemeral_key.public_key().public_numbers().x.to_bytes(32, "big")
            ),
            "y": base64url_encode(
                ephemeral_key.public_key().public_numbers().y.to_bytes(32, "big")
            ),
            "kty": "EC",
            "crv": "P-256",
        },
        "typ": "platformsso-login-response+jwt",
        "alg": "ECDH-ES",
        "apu": base64url_encode(apu),
        "apv": base64url_encode(apv),
    }

    party_u_info = length_prefixed(apu)
    party_v_info = length_prefixed(apv)
    supp_pub_info = (256).to_bytes(4, "big")

    other_info = length_prefixed(b"A256GCM") + party_u_info + party_v_info + supp_pub_info

    ckdf = ConcatKDFHash(
        algorithm=hashes.SHA256(),
        length=32,
        otherinfo=other_info,
    )

    derived_key = ckdf.derive(shared_secret_z)

    nonce = token_bytes(12)

    header_json = dumps(jwe_header, separators=(",", ":")).encode()
    aad = urlsafe_b64encode(header_json).rstrip(b"=")

    aesgcm = AESGCM(derived_key)
    ciphertext = aesgcm.encrypt(nonce, dumps(body).encode(), aad)

    ciphertext_body = ciphertext[:-16]
    tag = ciphertext[-16:]

    # base64url encoding
    protected_b64 = urlsafe_b64encode(header_json).rstrip(b"=")
    iv_b64 = urlsafe_b64encode(nonce).rstrip(b"=")
    ciphertext_b64 = urlsafe_b64encode(ciphertext_body).rstrip(b"=")
    tag_b64 = urlsafe_b64encode(tag).rstrip(b"=")

    jwe_compact = b".".join(
        [
            protected_b64,
            b"",
            iv_b64,
            ciphertext_b64,
            tag_b64,
        ]
    )
    return jwe_compact.decode()


class JWEResponse(HttpResponse):

    def __init__(
        self,
        data: dict,
        device: AppleDevice,
        apv: str,
    ):
        super().__init__(
            content=encrypt_token_with_a256_gcm(data, device.encryption_key, base64url_decode(apv)),
            content_type="application/platformsso-login-response+jwt",
        )
