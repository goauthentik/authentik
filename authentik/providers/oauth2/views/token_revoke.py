"""Token revocation endpoint"""
from dataclasses import dataclass

from django.http import Http404, HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from structlog.stdlib import get_logger

from authentik.providers.oauth2.errors import TokenRevocationError
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider, RefreshToken
from authentik.providers.oauth2.utils import TokenResponse, authenticate_provider

LOGGER = get_logger()


@dataclass(slots=True)
class TokenRevocationParams:
    """Parameters for Token Revocation"""

    token: RefreshToken | AccessToken
    provider: OAuth2Provider

    @staticmethod
    def from_request(request: HttpRequest) -> "TokenRevocationParams":
        """Extract required Parameters from HTTP Request"""
        raw_token = request.POST.get("token")

        provider = authenticate_provider(request)
        if not provider:
            raise TokenRevocationError("invalid_client")

        access_token = AccessToken.objects.filter(token=raw_token).first()
        if access_token:
            return TokenRevocationParams(access_token, provider)
        refresh_token = RefreshToken.objects.filter(token=raw_token).first()
        if refresh_token:
            return TokenRevocationParams(refresh_token, provider)
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
            return TokenResponse(exc.create_dict(), status=401)
        except Http404:
            # Token not found should return a HTTP 200
            # https://datatracker.ietf.org/doc/html/rfc7009#section-2.2
            return TokenResponse(data={}, status=200)
