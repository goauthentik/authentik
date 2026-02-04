"""OAuth2 logout utilities"""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.http import HttpRequest

from authentik.outposts.tasks import hash_session_key
from authentik.providers.oauth2.models import OAuth2Provider


def build_frontchannel_logout_url(
    provider: OAuth2Provider,
    request: HttpRequest,
    session_key: str | None = None,
) -> str | None:
    """Build frontchannel logout URL with iss and sid parameters.

    Returns None if provider doesn't have a logout_uri configured.
    """
    if not provider.logout_uri:
        return None

    parsed_url = urlparse(provider.logout_uri)

    query_params = {"iss": provider.get_issuer(request)}
    if session_key:
        query_params["sid"] = hash_session_key(session_key)

    # Preserve existing query params
    if parsed_url.query:
        existing_params = parse_qs(parsed_url.query, keep_blank_values=True)
        for key, value in existing_params.items():
            if key not in query_params:
                query_params[key] = value[0] if len(value) == 1 else value

    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            urlencode(query_params),
            parsed_url.fragment,
        )
    )
