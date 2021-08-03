"""authentik OAuth2 JWKS Views"""
from base64 import urlsafe_b64encode

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from authentik.core.models import Application
from authentik.providers.oauth2.models import JWTAlgorithms, OAuth2Provider


def b64_enc(number: int) -> str:
    """Convert number to base64-encoded octet-value"""
    length = ((number).bit_length() + 7) // 8
    number_bytes = number.to_bytes(length, "big")
    final = urlsafe_b64encode(number_bytes).rstrip(b"=")
    return final.decode("ascii")


class JWKSView(View):
    """Show RSA Key data for Provider"""

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Show RSA Key data for Provider"""
        application = get_object_or_404(Application, slug=application_slug)
        provider: OAuth2Provider = get_object_or_404(OAuth2Provider, pk=application.provider_id)

        response_data = {}

        if provider.jwt_alg == JWTAlgorithms.RS256 and provider.rsa_key:
            public_key: RSAPublicKey = provider.rsa_key.private_key.public_key()
            public_numbers = public_key.public_numbers()
            response_data["keys"] = [
                {
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "kid": provider.rsa_key.kid,
                    "n": b64_enc(public_numbers.n),
                    "e": b64_enc(public_numbers.e),
                }
            ]

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
