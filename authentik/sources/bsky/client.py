from typing import Any
from urllib.parse import urlparse

from django.core.cache import cache

from authentik.lib.utils.http import get_http_session
from authentik.sources.bsky.keys import sign_dpop_proof
from authentik.sources.bsky.models import BskySource
from authentik.sources.bsky.resolver import ResolutionError


def dpop_request(
    source: BskySource,
    method: str,
    url: str,
    data: dict[str, Any] | None = None,
    access_token: str | None = None,
) -> dict[str, Any]:
    nonce_key = f"bsky_dpop_nonce_{source.slug}_{urlparse(url).netloc}"
    nonce = cache.get(nonce_key)
    for _ in range(2):
        proof = sign_dpop_proof(source, method, url, nonce=nonce, access_token=access_token)
        headers = {"DPoP": proof}
        if access_token:
            headers["Authorization"] = f"DPoP {access_token}"
        resp = get_http_session().request(method, url, data=data, headers=headers)
        if resp.status_code in (400, 401) and resp.json().get("error") == "use_dpop_nonce":
            nonce = resp.headers["DPoP-Nonce"]
            cache.set(nonce_key, nonce, timeout=300)
            continue
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        return result
    raise ResolutionError("DPoP nonce retry exhausted")
