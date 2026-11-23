from datetime import datetime
from typing import NoReturn

from django.http import HttpRequest

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
        if self.refresh_token.dpop_jkt:
            self.validate_dpop(
                request,
                self.refresh_token.dpop_jkt,
                flow_name="refresh token",
            )

    def claim(self, now: datetime, rotate: bool) -> bool:
        """Decide whether this request may use the refresh token, and if `rotate` is set,
        consume it so that a successor may be issued. Must be called in the same transaction
        which issues the new tokens.

        Every path which allows a request to proceed is a single conditional update, never a
        read followed by a write, so that concurrent requests presenting the same token can't
        all pass the check: of those presenting an active token, exactly one consumes it, and
        the others are handled like reuse of a rotated token (which they are)."""
        token = self.refresh_token
        if not token.revoked:
            token.start_family()
            if not rotate:
                # The token stays valid, there's nothing to consume
                return True
            if token.consume(now):
                return True
            # Rotated by a concurrent request presenting the same token, which has committed
            # (`consume` waited for its row lock), so the successor it issued is visible now
            token.refresh_from_db()
        # Reuse of a rotated token. The grace period hooks in here; it must stay a single
        # conditional update (see `RefreshToken.claim_reuse_grace`) so that it can't race with
        # rotation either.
        return self.claim_reuse_grace(now)

    def claim_reuse_grace(self, now: datetime) -> bool:
        """Allow a rotated token to be used again within the grace period, for clients which
        retry or send concurrent refresh requests. Only when family revocation is enabled"""
        if not self.provider.refresh_token_revoke_family_on_reuse:
            return False
        grace_period = timedelta_from_string(self.provider.refresh_token_reuse_grace_period)
        if grace_period.total_seconds() <= 0:
            return False
        if not self.refresh_token.claim_reuse_grace(now - grace_period):
            return False
        self.logger.info("Rotated refresh token reused within grace period")
        return True

    def reject_reuse(self, request: HttpRequest) -> NoReturn:
        """A revoked refresh token was used, outside the grace period. This indicates the token
        may have been stolen, so revoke its family (if configured).
        https://datatracker.ietf.org/doc/html/rfc9700#section-4.14.2"""
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
