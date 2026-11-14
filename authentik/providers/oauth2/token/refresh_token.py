from django.http import HttpRequest
from django.utils.timezone import now

from authentik.events.models import Event, EventAction
from authentik.lib.utils.time import timedelta_from_string
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
            RefreshToken.token_query(raw_token), provider=self.provider
        ).first()
        if not self.refresh_token:
            self.logger.warning("Refresh token does not exist")
            raise TokenError("invalid_grant")
        if self.refresh_token.is_expired:
            self.logger.warning("Refresh token is expired")
            raise TokenError("invalid_grant")
        # https://datatracker.ietf.org/doc/html/rfc6749#section-6
        # Fallback to original token's scopes when none are given
        if not self.scope:
            self.scope = self.refresh_token.scope
        if self.refresh_token.revoked:
            self.handle_revoked(request)

        if self.refresh_token.dpop_jkt:
            self.validate_dpop(
                request,
                self.refresh_token.dpop_jkt,
                flow_name="refresh token",
            )

    def handle_revoked(self, request: HttpRequest) -> None:
        """A revoked refresh token was used. Unless it is a retry within the grace period, this
        indicates the token may have been stolen, so revoke its family (if configured).
        https://datatracker.ietf.org/doc/html/rfc9700#section-4.14.2"""
        if self.is_within_reuse_grace_period():
            self.logger.info("Rotated refresh token reused within grace period")
            return
        self.logger.warning("Refresh token is revoked")
        revoke_family = self.provider.refresh_token_revoke_family_on_reuse
        if revoke_family:
            self.refresh_token.revoke_family()
        Event.new(
            action=EventAction.SUSPICIOUS_REQUEST,
            message="Revoked refresh token was used",
            token=self.refresh_token,
            provider=self.refresh_token.provider,
            family_revoked=revoke_family,
        ).from_http(request, user=self.refresh_token.user)
        raise TokenError("invalid_grant")

    def is_within_reuse_grace_period(self) -> bool:
        """Check if the revoked refresh token may still be used, because it is the most
        recently rotated token of a family which is still active, and it was rotated within
        the grace period"""
        token = self.refresh_token
        if not self.provider.refresh_token_revoke_family_on_reuse:
            return False
        # Only tokens revoked by rotation have `rotated_at` set; never fall through to
        # `family=None`, which would match every token without a family
        if not token.rotated_at or not token.family:
            return False
        grace_period = timedelta_from_string(self.provider.refresh_token_reuse_grace_period)
        if token.rotated_at <= now() - grace_period:
            return False
        family = RefreshToken.objects.filter(family=token.family)
        # Another token was rotated since, so this one isn't the most recently rotated
        if family.filter(rotated_at__gt=token.rotated_at).exists():
            return False
        # The family has been revoked (or its active token revoked via RFC 7009)
        return family.filter(revoked=False).exists()
