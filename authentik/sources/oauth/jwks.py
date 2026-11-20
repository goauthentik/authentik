"""Fetch an OAuth source's signing keys (JWKS)"""

from re import IGNORECASE
from re import compile as re_compile

from requests import Response

from authentik.lib.utils.http import get_http_session
from authentik.sources.oauth.models import OAuthSource

# How long fetched keys are used for when the response doesn't say
JWKS_CACHE_SECONDS = 60 * 60
CACHE_CONTROL_MAX_AGE = re_compile(r"(?:^|,)\s*max-age\s*=\s*\"?(\d+)\"?\s*(?:,|$)", IGNORECASE)


def cache_max_age(response: Response, default: int = JWKS_CACHE_SECONDS) -> int:
    """The response's Cache-Control max-age (RFC 9111 §5.2.2.1) in seconds, else `default`"""
    match = CACHE_CONTROL_MAX_AGE.search(response.headers.get("Cache-Control", ""))
    return int(match.group(1)) if match else default


def refresh_jwks(source: OAuthSource, jwks_uri: str | None = None) -> int:
    """Fetch the keys at `jwks_uri` (the source's JWKS URL by default) and store them, and the
    URL they came from, on the source when they changed. Returns how long they may be used
    before they're fetched again: the response's Cache-Control max-age, else
    JWKS_CACHE_SECONDS. Raises RequestException when they can't be fetched, and ValueError when
    they aren't a JWK Set."""
    jwks_uri = jwks_uri or source.oidc_jwks_url
    response = get_http_session().get(jwks_uri)
    response.raise_for_status()
    jwks = response.json()
    # RFC 7517 §5: a JWK Set is an object with a "keys" array
    if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
        raise ValueError("Not a JWK Set")
    if source.oidc_jwks_url != jwks_uri or source.oidc_jwks != jwks:
        source.oidc_jwks_url = jwks_uri
        source.oidc_jwks = jwks
        source.save(update_fields=["oidc_jwks_url", "oidc_jwks"])
    return cache_max_age(response)
