"""authentik OAuth2 Token Introspection Views"""
from dataclasses import dataclass, field

from django.http import HttpRequest, HttpResponse
from django.views import View
from structlog.stdlib import get_logger

from authentik.providers.oauth2.errors import TokenIntrospectionError
from authentik.providers.oauth2.models import IDToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.utils import (
    TokenResponse,
    extract_access_token,
    extract_client_auth,
)

LOGGER = get_logger()


@dataclass
class TokenIntrospectionParams:
    """Parameters for Token Introspection"""

    token: RefreshToken

    provider: OAuth2Provider = field(init=False)
    id_token: IDToken = field(init=False)

    def __post_init__(self):
        if self.token.is_expired:
            LOGGER.debug("Token is not valid")
            raise TokenIntrospectionError()

        self.provider = self.token.provider
        self.id_token = self.token.id_token

        if not self.token.id_token:
            LOGGER.debug(
                "token not an authentication token",
                token=self.token,
            )
            raise TokenIntrospectionError()

    def authenticate_basic(self, request: HttpRequest) -> bool:
        """Attempt to authenticate via Basic auth of client_id:client_secret"""
        client_id, client_secret = extract_client_auth(request)
        if client_id == client_secret == "":
            return False
        if client_id != self.provider.client_id or client_secret != self.provider.client_secret:
            LOGGER.debug("(basic) Provider for basic auth does not exist")
            raise TokenIntrospectionError()
        return True

    def authenticate_bearer(self, request: HttpRequest) -> bool:
        """Attempt to authenticate via token sent as bearer header"""
        body_token = extract_access_token(request)
        if not body_token:
            return False
        tokens = RefreshToken.objects.filter(access_token=body_token).select_related("provider")
        if not tokens.exists():
            LOGGER.debug("(bearer) Token does not exist")
            raise TokenIntrospectionError()
        if tokens.first().provider != self.provider:
            LOGGER.debug("(bearer) Token providers don't match")
            raise TokenIntrospectionError()
        return True

    @staticmethod
    def from_request(request: HttpRequest) -> "TokenIntrospectionParams":
        """Extract required Parameters from HTTP Request"""
        raw_token = request.POST.get("token")
        token_type_hint = request.POST.get("token_type_hint", "access_token")
        token_filter = {token_type_hint: raw_token}

        if token_type_hint not in ["access_token", "refresh_token"]:
            LOGGER.debug("token_type_hint has invalid value", value=token_type_hint)
            raise TokenIntrospectionError()

        try:
            token: RefreshToken = RefreshToken.objects.select_related("provider").get(
                **token_filter
            )
        except RefreshToken.DoesNotExist:
            LOGGER.debug("Token does not exist", token=raw_token)
            raise TokenIntrospectionError()

        params = TokenIntrospectionParams(token=token)
        if not any([params.authenticate_basic(request), params.authenticate_bearer(request)]):
            LOGGER.warning("Not authenticated")
            raise TokenIntrospectionError()
        return params


class TokenIntrospectionView(View):
    """Token Introspection
    https://tools.ietf.org/html/rfc7662"""

    token: RefreshToken
    params: TokenIntrospectionParams
    provider: OAuth2Provider

    def post(self, request: HttpRequest) -> HttpResponse:
        """Introspection handler"""
        try:
            self.params = TokenIntrospectionParams.from_request(request)

            response_dic = {}
            if self.params.id_token:
                token_dict = self.params.id_token.to_dict()
                for k in ("aud", "sub", "exp", "iat", "iss"):
                    response_dic[k] = token_dict[k]
            response_dic["active"] = True
            response_dic["client_id"] = self.params.token.provider.client_id

            return TokenResponse(response_dic)
        except TokenIntrospectionError:
            return TokenResponse({"active": False})
