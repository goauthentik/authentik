from urllib.parse import quote

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from authentik.lib.generators import generate_id
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.sources.bsky.client import dpop_request
from authentik.sources.bsky.keys import sign_client_assertion
from authentik.sources.bsky.models import BskySource
from authentik.sources.bsky.resolver import resolve_identity


class BskyLoginView(View):
    def get(self, request: HttpRequest, source_slug: str) -> HttpResponse:
        source = get_object_or_404(BskySource, slug=source_slug)
        identifier = request.GET.get("identifier")
        if not identifier:
            return HttpResponseBadRequest("Missing identifier")

        identity = resolve_identity(identifier)
        verifier = generate_id(length=128)
        code_challenge = pkce_s256_challenge(verifier)

        callback_url = request.build_absolute_uri(
            reverse(
                "authentik_sources_bsky:oauth-client-callback", kwargs={"source_slug": source.slug}
            )
        )
        par_endpoint = identity.authserver_metadata["pushed_authorization_request_endpoint"]
        client_id = source.client_id(request)
        state = generate_id()

        par_response = dpop_request(
            source,
            "POST",
            par_endpoint,
            data={
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": callback_url,
                "scope": source.scope,
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "login_hint": identity.handle,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": sign_client_assertion(
                    source, request, identity.authserver_metadata["issuer"]
                ),
            },
        )

        request.session[f"bsky_{source.slug}_{state}"] = {
            "code_verifier": verifier,
            "authserver_url": identity.authserver_url,
            "token_endpoint": identity.authserver_metadata["token_endpoint"],
            "issuer": identity.authserver_metadata["issuer"],
            "did": identity.did,
            "pds_url": identity.pds_url,
        }
        auth_endpoint = identity.authserver_metadata["authorization_endpoint"]
        return redirect(
            f"{auth_endpoint}?client_id={quote(client_id)}&request_uri={quote(par_response['request_uri'])}"
        )
