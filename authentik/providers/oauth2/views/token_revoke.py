"""Token revocation endpoint"""

from dataclasses import dataclass

from django.http import Http404, HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.providers.oauth2.errors import TokenRevocationError
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.utils import (
    TokenResponse,
    authenticate_client,
    client_from_request,
    find_client_token,
)

LOGGER = get_logger()


@dataclass(slots=True)
class TokenRevocationParams:
    """Parameters for Token Revocation"""

    token: RefreshToken | AccessToken
    provider: OAuth2Provider

    @staticmethod
    def from_request(request: HttpRequest) -> TokenRevocationParams:
        """Extract required Parameters from HTTP Request"""
        raw_token = request.POST.get("token", "")

        client, _, _ = client_from_request(request)
        if client and client.is_confidential:
            client = authenticate_client(request)
        if not client:
            raise TokenRevocationError("invalid_client")
        # By default clients can only revoke their own tokens. If the request is
        # authenticated by a confidential client, it can also revoke federated tokens
        token = find_client_token(raw_token, client, include_federated=client.is_confidential)
        if token:
            return TokenRevocationParams(token, client.provider)
        LOGGER.debug("Token does not exist", token=raw_token)
        raise Http404


@method_decorator(csrf_exempt, name="dispatch")
class TokenRevokeView(View):
    """Token revoke endpoint
    https://datatracker.ietf.org/doc/html/rfc7009"""

    token: RefreshToken
    params: TokenRevocationParams
    provider: OAuth2Provider

    def post(self, request: HttpRequest) -> HttpResponse:
        """Revocation handler"""
        try:
            self.params = TokenRevocationParams.from_request(request)

            self.params.token.delete()

            return TokenResponse(data={}, status=200)
        except TokenRevocationError as exc:
            return TokenResponse(exc.create_dict(request), status=401)
        except Http404:
            # Token not found should return a HTTP 200
            # https://datatracker.ietf.org/doc/html/rfc7009#section-2.2
            return TokenResponse(data={}, status=200)
