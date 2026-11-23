"""authentik OAuth2 JWKS Views"""

from base64 import b64encode, urlsafe_b64encode
from collections.abc import Generator
from typing import Literal

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ec import (
    SECP256R1,
    SECP384R1,
    SECP521R1,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import Certificate
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.views import View
from jwt.utils import base64url_encode

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.jwt_mldsa import MLDSAKey
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


def _jwks_from_public_key(public_key: PublicKeyTypes, cert: Certificate, kid: str, use: str):
    """Convert given public key and certificate into JWKS data"""
    key_data = {}
    if isinstance(public_key, RSAPublicKey):
        public_numbers = public_key.public_numbers()
        key_data["kid"] = kid
        key_data["kty"] = "RSA"
        key_data["use"] = use
        key_data["n"] = to_base64url_uint(public_numbers.n).decode()
        key_data["e"] = to_base64url_uint(public_numbers.e).decode()
    elif isinstance(public_key, EllipticCurvePublicKey):
        public_numbers = public_key.public_numbers()
        curve_type = type(public_key.curve)
        key_data["kid"] = kid
        key_data["kty"] = "EC"
        key_data["use"] = use
        key_data["x"] = to_base64url_uint(public_numbers.x, min_length_map[curve_type]).decode()
        key_data["y"] = to_base64url_uint(public_numbers.y, min_length_map[curve_type]).decode()
        key_data["crv"] = ec_crv_map.get(curve_type, public_key.curve.name)
    elif isinstance(public_key, Ed25519PublicKey | Ed448PublicKey):
        key_data["kid"] = kid
        key_data["kty"] = "OKP"
        key_data["use"] = use
        key_data["crv"] = "Ed25519" if isinstance(public_key, Ed25519PublicKey) else "Ed448"
        key_data["x"] = base64url_encode(public_key.public_bytes_raw()).decode()
    elif isinstance(public_key, MLDSAKey):
        # RFC 9964: ML-DSA keys use the AKP key type with the raw public key in `pub`
        key_data["kid"] = kid
        key_data["kty"] = "AKP"
        key_data["use"] = use
        key_data["pub"] = base64url_encode(public_key.public_bytes_raw()).decode()
    else:
        return key_data
    key_data["x5c"] = [b64encode(cert.public_bytes(Encoding.DER)).decode("utf-8")]
    key_data["x5t"] = (
        urlsafe_b64encode(cert.fingerprint(hashes.SHA1())).decode("utf-8").rstrip("=")  # nosec
    )
    key_data["x5t#S256"] = (
        urlsafe_b64encode(cert.fingerprint(hashes.SHA256())).decode("utf-8").rstrip("=")
    )
    return key_data


class JWKSView(View):
    """Show RSA Key data for Provider"""

    @staticmethod
    def get_jwk_for_key(key: CertificateKeyPair, use: Literal["sig", "enc"]) -> dict | None:
        """Convert a certificate-key pair into JWK"""
        public_key = key.public_key
        key_data = None
        if not public_key:
            return key_data
        cert = key.certificate

        key_data = _jwks_from_public_key(public_key, cert, key.kid, use)

        if use == "sig":
            key_data["alg"] = JWTAlgorithms.from_public_key(public_key)
        elif use == "enc":
            key_data["alg"] = "RSA-OAEP-256"
            key_data["enc"] = "A256CBC-HS512"

        return key_data

    def get_keys(self) -> Generator[dict | None]:
        provider_ids = Application.objects.filter(
            slug=self.kwargs["application_slug"],
        ).values_list(
            "provider_id",
            flat=True,
        )
        provider = (
            OAuth2Provider.objects.select_related("signing_key", "encryption_key")
            .filter(pk__in=provider_ids)
            .first()
        )

        if provider is None:
            raise Http404()

        if signing_key := provider.signing_key:
            yield JWKSView.get_jwk_for_key(signing_key, "sig")
        if encryption_key := provider.encryption_key:
            yield JWKSView.get_jwk_for_key(encryption_key, "enc")

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Show JWK Key data for Provider"""
        response_data = {}
        for jwk in self.get_keys():
            if jwk:
                response_data.setdefault("keys", [])
                response_data["keys"].append(jwk)

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
