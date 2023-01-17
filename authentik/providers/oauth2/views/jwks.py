"""authentik OAuth2 JWKS Views"""
from base64 import b64encode, urlsafe_b64encode
from typing import Optional

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

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import JWTAlgorithms, OAuth2Provider


def b64_enc(number: int) -> str:
    """Convert number to base64-encoded octet-value"""
    length = ((number).bit_length() + 7) // 8
    number_bytes = number.to_bytes(length, "big")
    final = urlsafe_b64encode(number_bytes).rstrip(b"=")
    return final.decode("ascii")


# See https://notes.salrahman.com/generate-es256-es384-es512-private-keys/
# and _CURVE_TYPES in the same file as the below curve files
ec_crv_map = {
    SECP256R1: "P-256",
    SECP384R1: "P-384",
    SECP521R1: "P-512",
}


class JWKSView(View):
    """Show RSA Key data for Provider"""

    def get_jwk_for_key(self, key: CertificateKeyPair, exclude_x5=False) -> Optional[dict]:
        """Convert a certificate-key pair into JWK"""
        private_key = key.private_key
        key_data = None
        if not private_key:
            return key_data
        if isinstance(private_key, RSAPrivateKey):
            public_key: RSAPublicKey = private_key.public_key()
            public_numbers = public_key.public_numbers()
            key_data = {
                "kid": key.kid,
                "kty": "RSA",
                "alg": JWTAlgorithms.RS256,
                "use": "sig",
                "n": b64_enc(public_numbers.n),
                "e": b64_enc(public_numbers.e),
            }
        elif isinstance(private_key, EllipticCurvePrivateKey):
            public_key: EllipticCurvePublicKey = private_key.public_key()
            public_numbers = public_key.public_numbers()
            key_data = {
                "kid": key.kid,
                "kty": "EC",
                "alg": JWTAlgorithms.ES256,
                "use": "sig",
                "x": b64_enc(public_numbers.x),
                "y": b64_enc(public_numbers.y),
                "crv": ec_crv_map.get(type(public_key.curve), public_key.curve.name),
            }
        else:
            return key_data
        if not exclude_x5:
            key_data["x5c"] = [
                b64encode(key.certificate.public_bytes(Encoding.DER)).decode("utf-8")
            ]
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
        signing_key: CertificateKeyPair = provider.signing_key

        response_data = {}

        if signing_key:
            jwk = self.get_jwk_for_key(signing_key, "exclude_x5" in self.request.GET)
            if jwk:
                response_data["keys"] = [jwk]

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
