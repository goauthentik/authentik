from django.http import HttpRequest

from authentik.common.oauth.constants import PKCE_METHOD_S256, SCOPE_BOUND_KEY
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import AuthorizationCode
from authentik.providers.oauth2.token.base import TokenRequest
from authentik.providers.oauth2.utils import pkce_s256_challenge


class AuthorizationCodeTokenRequest(TokenRequest):

    authorization_code: AuthorizationCode | None = None

    def parse(self, request: HttpRequest) -> None:
        super().parse(request)
        raw_code = request.POST.get("code", "")
        if not raw_code:
            self.logger.warning("Missing authorization code")
            raise TokenError("invalid_grant")

        # Registered clients are checked against their configured redirect URIs. Other
        # clients may have none here, and are checked against the code's redirect URI below
        if self.client.is_legacy:
            self.check_redirect_uri(request)

        self.authorization_code = AuthorizationCode.objects.filter(code=raw_code).first()
        if not self.authorization_code:
            self.logger.warning("Code does not exist", code=raw_code)
            raise TokenError("invalid_grant")

        if self.authorization_code.is_expired:
            self.logger.warning(
                "Code is expired",
                token=raw_code,
            )
            raise TokenError("invalid_grant")

        if not self.authorization_code.is_bound_to(self.client):
            self.logger.warning("Invalid code: issued to a different client")
            raise TokenError("invalid_grant")

        # Clients other than registered ones must redeem the code with the exact redirect
        # URI it was authorized for. Registered clients keep being checked against their
        # configured redirect URIs only.
        if not self.client.is_legacy and (
            not self.authorization_code.redirect_uri
            or self.authorization_code.redirect_uri != self.redirect_uri
        ):
            self.logger.warning("Invalid code: redirect URI does not match authorization")
            raise TokenError("invalid_grant")

        # Enforce the client's PKCE requirements again, so that a code issued without
        # satisfying them can never be redeemed (no downgrade)
        if self.client.pkce_required and not self.authorization_code.code_challenge:
            self.logger.warning("Invalid code: issued without PKCE, which the client requires")
            raise TokenError("invalid_grant").with_cause("pkce_challenge_missing")
        allowed_methods = self.client.pkce_methods
        if (
            self.authorization_code.code_challenge
            and allowed_methods is not None
            and self.authorization_code.code_challenge_method not in allowed_methods
        ):
            self.logger.warning(
                "Invalid code: issued with a PKCE method the client may not use",
                method=self.authorization_code.code_challenge_method,
            )
            raise TokenError("invalid_grant").with_cause("pkce_method_not_allowed")

        # Validate PKCE parameters.
        if self.authorization_code.code_challenge:
            # Authorization code had PKCE but we didn't get one
            if not self.code_verifier:
                raise TokenError("invalid_grant")
            if self.authorization_code.code_challenge_method == PKCE_METHOD_S256:
                new_code_challenge = pkce_s256_challenge(self.code_verifier)
            else:
                new_code_challenge = self.code_verifier

            if new_code_challenge != self.authorization_code.code_challenge:
                self.logger.warning("Code challenge not matching")
                raise TokenError("invalid_grant")
        # Token request had a code_verifier but code did not have a code challenge
        # Prevent downgrade
        if not self.authorization_code.code_challenge and self.code_verifier:
            raise TokenError("invalid_grant")

        if SCOPE_BOUND_KEY in self.authorization_code.scope:
            self.validate_dpop(
                request,
                self.authorization_code.dpop_jkt,
                raw_code=raw_code,
                flow_name="authorization code",
            )

        self.resolve_resources(request, self.authorization_code.resources)
