"""authentik OAuth2 JWKS Views"""
from base64 import urlsafe_b64encode
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
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


class JWKSView(View):
    """Show RSA Key data for Provider"""

    def get_jwk_for_key(self, key: CertificateKeyPair) -> Optional[dict]:
        """Convert a certificate-key pair into JWK"""
        private_key = key.private_key
        if not private_key:
            return None
        if isinstance(private_key, RSAPrivateKey):
            public_key: RSAPublicKey = private_key.public_key()
            public_numbers = public_key.public_numbers()
            return {
                "kty": "RSA",
                "alg": JWTAlgorithms.RS256,
                "use": "sig",
                "kid": key.kid,
                "n": b64_enc(public_numbers.n),
                "e": b64_enc(public_numbers.e),
            }
        if isinstance(private_key, EllipticCurvePrivateKey):
            public_key: EllipticCurvePublicKey = private_key.public_key()
            public_numbers = public_key.public_numbers()
            return {
                "kty": "EC",
                "alg": JWTAlgorithms.ES256,
                "use": "sig",
                "kid": key.kid,
                "n": b64_enc(public_numbers.n),
                "e": b64_enc(public_numbers.e),
            }
        return None

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Show JWK Key data for Provider"""
        application = get_object_or_404(Application, slug=application_slug)
        provider: OAuth2Provider = get_object_or_404(OAuth2Provider, pk=application.provider_id)
        signing_key: CertificateKeyPair = provider.signing_key

        response_data = {}

        if signing_key:
            jwk = self.get_jwk_for_key(signing_key)
            if jwk:
                response_data["keys"] = [jwk]

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
