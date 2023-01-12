"""authentik OAuth2 Token Introspection Views"""
from dataclasses import dataclass, field

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.providers.oauth2.errors import TokenIntrospectionError
from authentik.providers.oauth2.models import IDToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.utils import TokenResponse, authenticate_provider

LOGGER = get_logger()


@dataclass
class TokenIntrospectionParams:
    """Parameters for Token Introspection"""

    token: RefreshToken
    provider: OAuth2Provider

    id_token: IDToken = field(init=False)

    def __post_init__(self):
        if self.token.is_expired:
            LOGGER.debug("Token is not valid")
            raise TokenIntrospectionError()

        self.id_token = self.token.id_token

        if not self.token.id_token:
            LOGGER.debug(
                "token not an authentication token",
                token=self.token,
            )
            raise TokenIntrospectionError()

    @staticmethod
    def from_request(request: HttpRequest) -> "TokenIntrospectionParams":
        """Extract required Parameters from HTTP Request"""
        raw_token = request.POST.get("token")
        token_type_hint = request.POST.get("token_type_hint", "access_token")
        token_filter = {token_type_hint: raw_token}

        if token_type_hint not in ["access_token", "refresh_token"]:
            LOGGER.debug("token_type_hint has invalid value", value=token_type_hint)
            raise TokenIntrospectionError()

        provider = authenticate_provider(request)
        if not provider:
            raise TokenIntrospectionError

        token: RefreshToken = RefreshToken.objects.filter(provider=provider, **token_filter).first()
        if not token:
            LOGGER.debug("Token does not exist", token=raw_token)
            raise TokenIntrospectionError()

        return TokenIntrospectionParams(token=token, provider=provider)


@method_decorator(csrf_exempt, name="dispatch")
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
                response_dic.update(self.params.id_token.to_dict())
            response_dic["active"] = True
            response_dic["client_id"] = self.params.token.provider.client_id

            return TokenResponse(response_dic)
        except TokenIntrospectionError:
            return TokenResponse({"active": False})
