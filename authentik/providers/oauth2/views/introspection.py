"""authentik OAuth2 Token Introspection Views"""
from dataclasses import dataclass, field

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.providers.oauth2.errors import TokenIntrospectionError
from authentik.providers.oauth2.models import AccessToken, IDToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.utils import TokenResponse, authenticate_provider

LOGGER = get_logger()


@dataclass(slots=True)
class TokenIntrospectionParams:
    """Parameters for Token Introspection"""

    token: RefreshToken | AccessToken
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
        provider = authenticate_provider(request)
        if not provider:
            raise TokenIntrospectionError

        access_token = AccessToken.objects.filter(token=raw_token).first()
        if access_token:
            return TokenIntrospectionParams(access_token, provider)
        refresh_token = RefreshToken.objects.filter(token=raw_token).first()
        if refresh_token:
            return TokenIntrospectionParams(refresh_token, provider)
        LOGGER.debug("Token does not exist", token=raw_token)
        raise TokenIntrospectionError()


@method_decorator(csrf_exempt, name="dispatch")
class TokenIntrospectionView(View):
    """Token Introspection
    https://datatracker.ietf.org/doc/html/rfc7662"""

    token: RefreshToken | AccessToken
    params: TokenIntrospectionParams
    provider: OAuth2Provider

    def post(self, request: HttpRequest) -> HttpResponse:
        """Introspection handler"""
        try:
            self.params = TokenIntrospectionParams.from_request(request)
            response = {}
            if self.params.id_token:
                response.update(self.params.id_token.to_dict())
            response["active"] = not self.params.token.is_expired and not self.params.token.revoked
            response["scope"] = " ".join(self.params.token.scope)
            response["client_id"] = self.params.provider.client_id
            return TokenResponse(response)
        except TokenIntrospectionError:
            return TokenResponse({"active": False})
