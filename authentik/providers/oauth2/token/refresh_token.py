from django.http import HttpRequest

from authentik.events.models import Event, EventAction
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import RefreshToken
from authentik.providers.oauth2.token.base import TokenRequest


class RefreshTokenTokenRequest(TokenRequest):

    refresh_token: RefreshToken | None = None

    def parse(self, request: HttpRequest) -> None:
        super().parse(request)
        raw_token = request.POST.get("refresh_token", "")
        if not raw_token:
            self.logger.warning("Missing refresh token")
            raise TokenError("invalid_grant")

        self.refresh_token = RefreshToken.objects.filter(
            token=raw_token, provider=self.provider
        ).first()
        if not self.refresh_token:
            self.logger.warning(
                "Refresh token does not exist",
                token=raw_token,
            )
            raise TokenError("invalid_grant")
        if self.refresh_token.is_expired:
            self.logger.warning(
                "Refresh token is expired",
                token=raw_token,
            )
            raise TokenError("invalid_grant")
        # https://datatracker.ietf.org/doc/html/rfc6749#section-6
        # Fallback to original token's scopes when none are given
        if not self.scope:
            self.scope = self.refresh_token.scope
        if self.refresh_token.revoked:
            self.logger.warning("Refresh token is revoked", token=raw_token)
            Event.new(
                action=EventAction.SUSPICIOUS_REQUEST,
                message="Revoked refresh token was used",
                token=self.refresh_token,
                provider=self.refresh_token.provider,
            ).from_http(request, user=self.refresh_token.user)
            raise TokenError("invalid_grant")

        if self.refresh_token.dpop_jkt:
            self.validate_dpop(
                request,
                self.refresh_token.dpop_jkt,
                flow_name="refresh token",
            )
