from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.providers.oauth2.views.jwks import JWKSView as OAuthJWKSView


class JWKSview(View):

    def get(self, request: HttpRequest, provider: int) -> HttpResponse:
        """Show JWK Key data for Provider"""
        provider: SSFProvider = get_object_or_404(SSFProvider, pk=provider)
        signing_key: CertificateKeyPair = provider.signing_key

        response_data = {}

        if signing_key:
            jwk = OAuthJWKSView.get_jwk_for_key(signing_key, "sig")
            if jwk:
                response_data["keys"] = [jwk]

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
