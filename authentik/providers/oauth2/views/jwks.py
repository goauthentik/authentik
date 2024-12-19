"""authentik OAuth2 JWKS Views"""

from base64 import b64encode, urlsafe_b64encode

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ec import (
    SECP256R1,
    SECP384R1,
    SECP521R1,
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.serialization import Encoding
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from jwt.utils import base64url_encode

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import JWTAlgorithms, OAuth2Provider

# See https://notes.salrahman.com/generate-es256-es384-es512-private-keys/
# and _CURVE_TYPES in the same file as the below curve files
ec_crv_map = {
    SECP256R1: "P-256",
    SECP384R1: "P-384",
    SECP521R1: "P-521",
}
min_length_map = {
    SECP256R1: 32,
    SECP384R1: 48,
    SECP521R1: 66,
}


# https://github.com/jpadilla/pyjwt/issues/709
def bytes_from_int(val: int, min_length: int = 0) -> bytes:
    """Custom bytes_from_int that accepts a minimum length"""
    remaining = val
    byte_length = 0

    while remaining != 0:
        remaining >>= 8
        byte_length += 1
    length = max([byte_length, min_length])
    return val.to_bytes(length, "big", signed=False)


def to_base64url_uint(val: int, min_length: int = 0) -> bytes:
    """Custom to_base64url_uint that accepts a minimum length"""
    if val < 0:
        raise ValueError("Must be a positive integer")

    int_bytes = bytes_from_int(val, min_length)

    if len(int_bytes) == 0:
        int_bytes = b"\x00"

    return base64url_encode(int_bytes)


class JWKSView(View):
    """Show RSA Key data for Provider"""

    @staticmethod
    def get_jwk_for_key(key: CertificateKeyPair, use: str) -> dict | None:
        """Convert a certificate-key pair into JWK"""
        private_key = key.private_key
        key_data = None
        if not private_key:
            return key_data

        key_data = {}

        if use == "sig":
            if isinstance(private_key, RSAPrivateKey):
                key_data["alg"] = JWTAlgorithms.RS256
            elif isinstance(private_key, EllipticCurvePrivateKey):
                key_data["alg"] = JWTAlgorithms.ES256
        elif use == "enc":
            key_data["alg"] = "RSA-OAEP-256"
            key_data["enc"] = "A256CBC-HS512"

        if isinstance(private_key, RSAPrivateKey):
            public_key: RSAPublicKey = private_key.public_key()
            public_numbers = public_key.public_numbers()
            key_data["kid"] = key.kid
            key_data["kty"] = "RSA"
            key_data["use"] = use
            key_data["n"] = to_base64url_uint(public_numbers.n).decode()
            key_data["e"] = to_base64url_uint(public_numbers.e).decode()
        elif isinstance(private_key, EllipticCurvePrivateKey):
            public_key: EllipticCurvePublicKey = private_key.public_key()
            public_numbers = public_key.public_numbers()
            curve_type = type(public_key.curve)
            key_data["kid"] = key.kid
            key_data["kty"] = "EC"
            key_data["use"] = use
            key_data["x"] = to_base64url_uint(public_numbers.x, min_length_map[curve_type]).decode()
            key_data["y"] = to_base64url_uint(public_numbers.y, min_length_map[curve_type]).decode()
            key_data["crv"] = ec_crv_map.get(curve_type, public_key.curve.name)
        else:
            return key_data
        key_data["x5c"] = [b64encode(key.certificate.public_bytes(Encoding.DER)).decode("utf-8")]
        key_data["x5t"] = (
            urlsafe_b64encode(key.certificate.fingerprint(hashes.SHA1()))  # nosec
            .decode("utf-8")
            .rstrip("=")
        )
        key_data["x5t#S256"] = (
            urlsafe_b64encode(key.certificate.fingerprint(hashes.SHA256()))
            .decode("utf-8")
            .rstrip("=")
        )
        return key_data

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Show JWK Key data for Provider"""
        application = get_object_or_404(Application, slug=application_slug)
        provider: OAuth2Provider = get_object_or_404(OAuth2Provider, pk=application.provider_id)

        response_data = {}

        if signing_key := provider.signing_key:
            jwk = JWKSView.get_jwk_for_key(signing_key, "sig")
            if jwk:
                response_data.setdefault("keys", [])
                response_data["keys"].append(jwk)
        if encryption_key := provider.encryption_key:
            jwk = JWKSView.get_jwk_for_key(encryption_key, "enc")
            if jwk:
                response_data.setdefault("keys", [])
                response_data["keys"].append(jwk)

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
