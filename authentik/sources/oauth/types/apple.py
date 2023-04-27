"""Apple OAuth Views"""
from time import time
from typing import Any, Optional

from django.http.request import HttpRequest
from django.urls.base import reverse
from jwt import decode, encode
from rest_framework.fields import CharField
from structlog.stdlib import get_logger

from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class AppleLoginChallenge(Challenge):
    """Special challenge for apple-native authentication flow, which happens on the client."""

    client_id = CharField()
    component = CharField(default="ak-source-oauth-apple")
    scope = CharField()
    redirect_uri = CharField()
    state = CharField()


class AppleChallengeResponse(ChallengeResponse):
    """Pseudo class for plex response"""

    component = CharField(default="ak-source-oauth-apple")


class AppleOAuthClient(OAuth2Client):
    """Apple OAuth2 client"""

    def get_client_id(self) -> str:
        parts: list[str] = self.source.consumer_key.split(";")
        if len(parts) < 3:
            return self.source.consumer_key
        return parts[0].strip()

    def get_client_secret(self) -> str:
        now = time()
        parts: list[str] = self.source.consumer_key.split(";")
        if len(parts) < 3:
            raise ValueError(
                "Apple Source client_id should be formatted like "
                "services_id_identifier;apple_team_id;key_id"
            )
        LOGGER.debug("got values from client_id", team=parts[1], kid=parts[2])
        payload = {
            "iss": parts[1].strip(),
            "iat": now,
            "exp": now + 86400 * 180,
            "aud": "https://appleid.apple.com",
            "sub": parts[0].strip(),
        }
        jwt = encode(payload, self.source.consumer_secret, "ES256", {"kid": parts[2].strip()})
        LOGGER.debug("signing payload as secret key", payload=payload, jwt=jwt)
        return jwt

    def get_profile_info(self, token: dict[str, str]) -> Optional[dict[str, Any]]:
        id_token = token.get("id_token")
        return decode(id_token, options={"verify_signature": False})


class AppleOAuthRedirect(OAuthRedirect):
    """Apple OAuth2 Redirect"""

    client_class = AppleOAuthClient

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["name", "email"],
            "response_mode": "form_post",
        }


class AppleOAuth2Callback(OAuthCallback):
    """Apple OAuth2 Callback"""

    client_class = AppleOAuthClient

    def get_user_id(self, info: dict[str, Any]) -> Optional[str]:
        return info["sub"]

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "email": info.get("email"),
            "name": info.get("name"),
        }


@registry.register()
class AppleType(SourceType):
    """Apple Type definition"""

    callback_view = AppleOAuth2Callback
    redirect_view = AppleOAuthRedirect
    name = "Apple"
    slug = "apple"

    authorization_url = "https://appleid.apple.com/auth/authorize"
    access_token_url = "https://appleid.apple.com/auth/token"  # nosec
    profile_url = ""

    def login_challenge(self, source: OAuthSource, request: HttpRequest) -> Challenge:
        """Pre-general all the things required for the JS SDK"""
        apple_client = AppleOAuthClient(
            source,
            request,
            callback=reverse(
                "authentik_sources_oauth:oauth-client-callback",
                kwargs={"source_slug": source.slug},
            ),
        )
        args = apple_client.get_redirect_args()
        return AppleLoginChallenge(
            instance={
                "client_id": apple_client.get_client_id(),
                "scope": "name email",
                "redirect_uri": args["redirect_uri"],
                "state": args["state"],
                "type": ChallengeTypes.NATIVE.value,
            }
        )
