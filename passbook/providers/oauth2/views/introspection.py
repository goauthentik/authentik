"""passbook OAuth2 Token Introspection Views"""
from dataclasses import InitVar, dataclass
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.views import View
from structlog import get_logger

from passbook.providers.oauth2.constants import SCOPE_OPENID_INTROSPECTION
from passbook.providers.oauth2.errors import TokenIntrospectionError
from passbook.providers.oauth2.models import IDToken, OAuth2Provider, RefreshToken
from passbook.providers.oauth2.utils import TokenResponse, extract_client_auth

LOGGER = get_logger()


@dataclass
class TokenIntrospectionParams:
    """Parameters for Token Introspection"""

    client_id: str
    client_secret: str

    raw_token: InitVar[str]

    token: Optional[RefreshToken] = None

    provider: Optional[OAuth2Provider] = None
    id_token: Optional[IDToken] = None

    def __post_init__(self, raw_token: str):
        try:
            self.token = RefreshToken.objects.get(access_token=raw_token)
        except RefreshToken.DoesNotExist:
            LOGGER.debug("Token does not exist", token=raw_token)
            raise TokenIntrospectionError()
        if self.token.has_expired():
            LOGGER.debug("Token is not valid", token=raw_token)
            raise TokenIntrospectionError()
        try:
            self.provider = OAuth2Provider.objects.get(
                client_id=self.client_id, client_secret=self.client_secret,
            )
        except OAuth2Provider.DoesNotExist:
            LOGGER.debug("provider for ID not found", client_id=self.client_id)
            raise TokenIntrospectionError()
        if SCOPE_OPENID_INTROSPECTION not in self.provider.scope_names:
            LOGGER.debug(
                "OAuth2Provider does not have introspection scope",
                client_id=self.client_id,
            )
            raise TokenIntrospectionError()

        self.id_token = self.token.id_token

        if not self.token.id_token:
            LOGGER.debug(
                "token not an authentication token", token=self.token,
            )
            raise TokenIntrospectionError()

        audience = self.token.id_token.aud
        if not audience:
            LOGGER.debug(
                "No audience found for token", token=self.token,
            )
            raise TokenIntrospectionError()

        if audience not in self.provider.scope_names:
            LOGGER.debug(
                "provider does not audience scope",
                client_id=self.client_id,
                audience=audience,
            )
            raise TokenIntrospectionError()

    @staticmethod
    def from_request(request: HttpRequest) -> "TokenIntrospectionParams":
        """Extract required Parameters from HTTP Request"""
        # Introspection only supports POST requests
        client_id, client_secret = extract_client_auth(request)
        return TokenIntrospectionParams(
            raw_token=request.POST.get("token"),
            client_id=client_id,
            client_secret=client_secret,
        )


class TokenIntrospectionView(View):
    """Token Introspection
    https://tools.ietf.org/html/rfc7662"""

    token: RefreshToken
    params: TokenIntrospectionParams
    provider: OAuth2Provider
    id_token: IDToken

    def post(self, request: HttpRequest) -> HttpResponse:
        """Introspection handler"""
        self.params = TokenIntrospectionParams.from_request(request)

        try:
            response_dic = {}
            if self.id_token:
                token_dict = self.id_token.to_dict()
                for k in ("aud", "sub", "exp", "iat", "iss"):
                    response_dic[k] = token_dict[k]
            response_dic["active"] = True
            response_dic["client_id"] = self.token.provider.client_id

            return TokenResponse(response_dic)
        except TokenIntrospectionError:
            return TokenResponse({"active": False})
