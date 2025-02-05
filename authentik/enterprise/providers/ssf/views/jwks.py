from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.providers.ssf.models import SSFProvider
from authentik.providers.oauth2.views.jwks import JWKSView as OAuthJWKSView


class JWKSview(View):
    """SSF JWKS endpoint, similar to the OAuth2 provider's endpoint"""

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Show JWK Key data for Provider"""
        application = get_object_or_404(Application, slug=application_slug)
        provider = application.backchannel_provider_for(SSFProvider)
        if not provider:
            raise Http404
        signing_key: CertificateKeyPair = provider.signing_key

        response_data = {}

        jwk = OAuthJWKSView.get_jwk_for_key(signing_key, "sig")
        if jwk:
            response_data["keys"] = [jwk]

        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "*"

        return response
