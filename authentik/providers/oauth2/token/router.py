"""Dispatch a token request to the request class implementing its grant type"""

from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_PASSWORD,
    GRANT_TYPE_REFRESH_TOKEN,
    GRANT_TYPE_TOKEN_EXCHANGE,
)
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.token.authorization_code import AuthorizationCodeTokenRequest
from authentik.providers.oauth2.token.base import TokenRequest
from authentik.providers.oauth2.token.client_credentials import ClientCredentialsTokenRequest
from authentik.providers.oauth2.token.device_code import DeviceCodeTokenRequest
from authentik.providers.oauth2.token.refresh_token import RefreshTokenTokenRequest
from authentik.providers.oauth2.token.token_exchange import TokenExchangeTokenRequest

LOGGER = get_logger()


def route_token_request(grant_type: str) -> type[TokenRequest]:
    if grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
        return AuthorizationCodeTokenRequest
    elif grant_type == GRANT_TYPE_REFRESH_TOKEN:
        return RefreshTokenTokenRequest
    elif grant_type == GRANT_TYPE_CLIENT_CREDENTIALS:
        return ClientCredentialsTokenRequest
    elif grant_type == GRANT_TYPE_PASSWORD:
        return ClientCredentialsTokenRequest
    elif grant_type == GRANT_TYPE_DEVICE_CODE:
        return DeviceCodeTokenRequest
    elif grant_type == GRANT_TYPE_TOKEN_EXCHANGE:
        return TokenExchangeTokenRequest
    raise TokenError("unsupported_grant_type")


def parse_token_request(
    request: HttpRequest, provider: OAuth2Provider, client_id: str, client_secret: str
) -> TokenRequest:
    grant_type = request.POST.get("grant_type", "")
    req_type = route_token_request(grant_type)
    LOGGER.debug("routing to token request", token_request_type=req_type)
    req = req_type(provider, client_id, client_secret)
    req.parse(request)
    return req
