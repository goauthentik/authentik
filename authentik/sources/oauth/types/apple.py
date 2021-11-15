"""Apple OAuth Views"""
from time import time
from typing import Any, Optional

from jwt import decode, encode
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.types.manager import MANAGER, SourceType
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class AppleOAuthClient(OAuth2Client):
    """Apple OAuth2 client"""

    def get_client_id(self) -> str:
        parts = self.source.consumer_key.split(";")
        if len(parts) < 3:
            return self.source.consumer_key
        return parts[0]

    def get_client_secret(self) -> str:
        now = time()
        parts = self.source.consumer_key.split(";")
        if len(parts) < 3:
            raise ValueError(
                (
                    "Apple Source client_id should be formatted like "
                    "services_id_identifier;apple_team_id;key_id"
                )
            )
        LOGGER.debug("got values from client_id", team=parts[1], kid=parts[2])
        payload = {
            "iss": parts[1],
            "iat": now,
            "exp": now + 86400 * 180,
            "aud": "https://appleid.apple.com",
            "sub": parts[0],
        }
        # pyright: reportGeneralTypeIssues=false
        jwt = encode(payload, self.source.consumer_secret, "ES256", {"kid": parts[2]})
        LOGGER.debug("signing payload as secret key", payload=payload, jwt=jwt)
        return jwt

    def get_profile_info(self, token: dict[str, str]) -> Optional[dict[str, Any]]:
        id_token = token.get("id_token")
        return decode(id_token, options={"verify_signature": False})


class AppleOAuthRedirect(OAuthRedirect):
    """Apple OAuth2 Redirect"""

    client_class = AppleOAuthClient

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": "name email",
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
        print(info)
        return {
            "email": info.get("email"),
            "name": info.get("name"),
        }


@MANAGER.type()
class AppleType(SourceType):
    """Apple Type definition"""

    callback_view = AppleOAuth2Callback
    redirect_view = AppleOAuthRedirect
    name = "Apple"
    slug = "apple"

    authorization_url = "https://appleid.apple.com/auth/authorize"
    access_token_url = "https://appleid.apple.com/auth/token"  # nosec
    profile_url = ""

    def icon_url(self) -> str:
        return "https://appleid.cdn-apple.com/appleid/button/logo"
