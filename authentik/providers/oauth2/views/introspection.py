"""authentik OAuth2 Token Introspection Views"""

from dataclasses import dataclass, field

from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.providers.oauth2.errors import TokenIntrospectionError
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.utils import TokenResponse, authenticate_client, find_client_token

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
            LOGGER.debug("token not an authentication token", token=self.token)
            raise TokenIntrospectionError()

    @staticmethod
    def from_request(request: HttpRequest) -> TokenIntrospectionParams:
        """Extract required Parameters from HTTP Request"""
        raw_token = request.POST.get("token", "")
        client = authenticate_client(request)
        if not client:
            LOGGER.info("Failed to authenticate introspection request")
            raise TokenIntrospectionError
        if not client.is_confidential:
            LOGGER.info("Introspection request from public provider, denying.")
            raise TokenIntrospectionError

        token = find_client_token(raw_token, client, include_federated=True)
        if token:
            return TokenIntrospectionParams(token, token.provider)
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
                response.pop("cnf", None)
            response["active"] = not self.params.token.is_expired and not self.params.token.revoked
            response["scope"] = " ".join(self.params.token.scope)
            response["client_id"] = self.params.token.bound_client_id
            if isinstance(self.params.token, AccessToken) and self.params.token.resource:
                response["aud"] = self.params.token.resource
            return TokenResponse(response)
        except TokenIntrospectionError:
            return TokenResponse({"active": False})
