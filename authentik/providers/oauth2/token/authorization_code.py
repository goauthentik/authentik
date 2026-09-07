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

        if self.authorization_code.provider != self.provider or self.authorization_code.is_expired:
            self.logger.warning("Invalid code: invalid client or code has expired")
            raise TokenError("invalid_grant")

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
