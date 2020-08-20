"""passbook OAuth2 Token views"""
from base64 import urlsafe_b64encode
from dataclasses import InitVar, dataclass
from hashlib import sha256
from typing import Any, Dict, List, Optional

from django.http import HttpRequest, HttpResponse
from django.views import View
from structlog import get_logger

from passbook.lib.utils.time import timedelta_from_string
from passbook.providers.oauth2.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
)
from passbook.providers.oauth2.errors import TokenError, UserAuthError
from passbook.providers.oauth2.models import (
    AuthorizationCode,
    OAuth2Provider,
    RefreshToken,
)
from passbook.providers.oauth2.utils import TokenResponse, extract_client_auth

LOGGER = get_logger()


@dataclass
# pylint: disable=too-many-instance-attributes
class TokenParams:
    """Token params"""

    client_id: str
    client_secret: str
    redirect_uri: str
    grant_type: str
    state: str
    scope: List[str]

    authorization_code: Optional[AuthorizationCode] = None
    refresh_token: Optional[RefreshToken] = None

    code_verifier: Optional[str] = None

    raw_code: InitVar[str] = ""
    raw_token: InitVar[str] = ""

    @staticmethod
    def from_request(request: HttpRequest) -> "TokenParams":
        """Extract Token Parameters from http request"""
        client_id, client_secret = extract_client_auth(request)

        return TokenParams(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=request.POST.get("redirect_uri", ""),
            grant_type=request.POST.get("grant_type", ""),
            raw_code=request.POST.get("code", ""),
            raw_token=request.POST.get("refresh_token", ""),
            state=request.POST.get("state", ""),
            scope=request.POST.get("scope", "").split(),
            # PKCE parameter.
            code_verifier=request.POST.get("code_verifier"),
        )

    def __post_init__(self, raw_code, raw_token):
        try:
            provider: OAuth2Provider = OAuth2Provider.objects.get(
                client_id=self.client_id
            )
            self.provider = provider
        except OAuth2Provider.DoesNotExist:
            LOGGER.warning("OAuth2Provider does not exist", client_id=self.client_id)
            raise TokenError("invalid_client")

        if self.provider.client_type == "confidential":
            if self.provider.client_secret != self.client_secret:
                LOGGER.warning(
                    "Invalid client secret: client does not have secret",
                    client_id=self.provider.client_id,
                    secret=self.provider.client_secret,
                )
                raise TokenError("invalid_client")

        if self.grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
            self.__post_init_code(raw_code)

        elif self.grant_type == GRANT_TYPE_REFRESH_TOKEN:
            if not raw_token:
                LOGGER.warning("Missing refresh token")
                raise TokenError("invalid_grant")

            try:
                self.refresh_token = RefreshToken.objects.get(
                    refresh_token=raw_token, client=self.provider
                )

            except RefreshToken.DoesNotExist:
                LOGGER.warning(
                    "Refresh token does not exist", token=raw_token,
                )
                raise TokenError("invalid_grant")

        else:
            LOGGER.warning("Invalid grant type", grant_type=self.grant_type)
            raise TokenError("unsupported_grant_type")

    def __post_init_code(self, raw_code):
        if not raw_code:
            LOGGER.warning("Missing authorization code")
            raise TokenError("invalid_grant")

        if self.redirect_uri not in self.provider.redirect_uris.split():
            LOGGER.warning("Invalid redirect uri", uri=self.redirect_uri, expected=self.provider.redirect_uris.split())
            raise TokenError("invalid_client")

        try:
            self.authorization_code = AuthorizationCode.objects.get(code=raw_code)
        except AuthorizationCode.DoesNotExist:
            LOGGER.warning("Code does not exist", code=raw_code)
            raise TokenError("invalid_grant")

        if (
            self.authorization_code.provider != self.provider
            or self.authorization_code.is_expired
        ):
            LOGGER.warning("Invalid code: invalid client or code has expired")
            raise TokenError("invalid_grant")

        # Validate PKCE parameters.
        if self.code_verifier:
            if self.authorization_code.code_challenge_method == "S256":
                new_code_challenge = (
                    urlsafe_b64encode(
                        sha256(self.code_verifier.encode("ascii")).digest()
                    )
                    .decode("utf-8")
                    .replace("=", "")
                )
            else:
                new_code_challenge = self.code_verifier

            if new_code_challenge != self.authorization_code.code_challenge:
                LOGGER.warning("Code challenge not matching")
                raise TokenError("invalid_grant")


class TokenView(View):
    """Generate tokens for clients"""

    params: TokenParams

    def post(self, request: HttpRequest) -> HttpResponse:
        """Generate tokens for clients"""
        try:
            self.params = TokenParams.from_request(request)

            if self.params.grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
                return TokenResponse(self.create_code_response_dic())
            if self.params.grant_type == GRANT_TYPE_REFRESH_TOKEN:
                return TokenResponse(self.create_refresh_response_dic())
            raise ValueError(f"Invalid grant_type: {self.params.grant_type}")
        except TokenError as error:
            return TokenResponse(error.create_dict(), status=400)
        except UserAuthError as error:
            return TokenResponse(error.create_dict(), status=403)

    def create_code_response_dic(self) -> Dict[str, Any]:
        """See https://tools.ietf.org/html/rfc6749#section-4.1"""

        refresh_token = self.params.authorization_code.provider.create_refresh_token(
            user=self.params.authorization_code.user,
            scope=self.params.authorization_code.scope,
        )

        if self.params.authorization_code.is_open_id:
            id_token = refresh_token.create_id_token(
                user=self.params.authorization_code.user, request=self.request,
            )
            id_token.nonce = self.params.authorization_code.nonce
            id_token.at_hash = refresh_token.at_hash
            refresh_token.id_token = id_token

        # Store the token.
        refresh_token.save()

        # We don't need to store the code anymore.
        self.params.authorization_code.delete()

        dic = {
            "access_token": refresh_token.access_token,
            "refresh_token": refresh_token.refresh_token,
            "token_type": "bearer",
            "expires_in": timedelta_from_string(
                self.params.provider.token_validity
            ).seconds,
            "id_token": refresh_token.id_token.encode(refresh_token.provider),
        }

        return dic

    def create_refresh_response_dic(self) -> Dict[str, Any]:
        """See https://tools.ietf.org/html/rfc6749#section-6"""

        unauthorized_scopes = set(self.params.scope) - set(
            self.params.refresh_token.scope
        )
        if unauthorized_scopes:
            raise TokenError("invalid_scope")

        refresh_token = self.params.refresh_token.provider.create_token(
            user=self.params.refresh_token.user,
            provider=self.params.refresh_token.provider,
            scope=self.params.scope,
        )

        # If the Token has an id_token it's an Authentication request.
        if self.params.refresh_token.id_token:
            refresh_token.id_token = refresh_token.create_id_token(
                user=self.params.refresh_token.user, request=self.request,
            )
            refresh_token.id_token.at_hash = refresh_token.at_hash

            # Store the refresh_token.
            refresh_token.save()

        # Forget the old token.
        self.params.refresh_token.delete()

        dic = {
            "access_token": refresh_token.access_token,
            "refresh_token": refresh_token.refresh_token,
            "token_type": "bearer",
            "expires_in": timedelta_from_string(
                refresh_token.provider.token_validity
            ).seconds,
            "id_token": refresh_token.id_token.encode(
                self.params.refresh_token.provider
            ),
        }

        return dic
