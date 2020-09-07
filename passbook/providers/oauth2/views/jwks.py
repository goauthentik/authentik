"""passbook OAuth2 JWKS Views"""
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from jwkest import long_to_base64
from jwkest.jwk import import_rsa_key

from passbook.core.models import Application
from passbook.providers.oauth2.models import JWTAlgorithms, OAuth2Provider


class JWKSView(View):
    """Show RSA Key data for Provider"""

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Show RSA Key data for Provider"""
        application = get_object_or_404(Application, slug=application_slug)
        provider: OAuth2Provider = get_object_or_404(
            OAuth2Provider, pk=application.provider_id
        )

        response_data = {}

        if provider.jwt_alg == JWTAlgorithms.RS256:
            public_key = import_rsa_key(provider.rsa_key.key_data).publickey()
            response_data["keys"] = [
                {
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "kid": provider.rsa_key.kid,
                    "n": long_to_base64(public_key.n),
                    "e": long_to_base64(public_key.e),
                }
            ]

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
