from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View

from authentik.providers.oauth2.dpop import jwk_thumbprint
from authentik.sources.bsky.keys import public_jwk
from authentik.sources.bsky.models import BskySource


class ClientMetadataView(View):
    def get(self, request: HttpRequest, source_slug: str) -> JsonResponse:
        source = get_object_or_404(BskySource, slug=source_slug)
        client_id = source.client_id(request)
        return JsonResponse(
            {
                "client_id": client_id,
                "client_name": source.name,
                "client_uri": request.build_absolute_uri("/"),
                "redirect_uris": [
                    request.build_absolute_uri(
                        reverse(
                            "authentik_sources_bsky:oauth-client-callback",
                            kwargs={"source_slug": source.slug},
                        )
                    )
                ],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "scope": source.scope,
                "token_endpoint_auth_method": "private_key_jwt",
                "token_endpoint_auth_signing_alg": "ES256",
                "dpop_bound_access_tokens": True,
                "application_type": "web",
                "jwks_uri": request.build_absolute_uri(
                    reverse(
                        "authentik_sources_bsky:oauth-client-jwks",
                        kwargs={"source_slug": source.slug},
                    )
                ),
            }
        )


class ClientJWKSView(View):
    def get(self, request: HttpRequest, source_slug: str) -> JsonResponse:
        source = get_object_or_404(BskySource, slug=source_slug)
        jwk = public_jwk(source)
        return JsonResponse(
            {
                "keys": [
                    {
                        **jwk,
                        "kid": jwk_thumbprint(jwk),
                        "use": "sig",
                        "alg": "ES256",
                    }
                ]
            }
        )
