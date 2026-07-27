"""Instagram OAuth Views"""

from typing import Any

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod, OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class InstagramOAuth2Client(OAuth2Client):
    """Instagram OAuth2 Client"""

    def get_access_token(self, **request_kwargs) -> dict[str, Any] | None:
        token = super().get_access_token(**request_kwargs)
        if token is None or "error" in token:
            return token
        # Instagram returns short-lived tokens wrapped in a single-element "data" array,
        # and omits token_type entirely
        # https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/business-login
        data = token.get("data")
        if data:
            token = dict(data[0])
        token.setdefault("token_type", "Bearer")
        return token


class InstagramOAuthRedirect(OAuthRedirect):
    """Instagram OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        # Instagram's authorize endpoint rejects the request with "Invalid platform app"
        # unless these are present, even when a valid Instagram App ID is used.
        # https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login
        return {
            "scope": ["instagram_business_basic"],
            "enable_fb_login": "0",
            "force_authentication": "1",
        }


class InstagramOAuthCallback(OAuthCallback):
    """Instagram OAuth2 Callback"""

    client_class = InstagramOAuth2Client

    def get_user_id(self, info: dict[str, Any]) -> str | None:
        user_id = info.get("user_id", info.get("id"))
        if not user_id:
            return None
        return str(user_id)


@registry.register()
class InstagramType(SourceType):
    """Instagram Type definition"""

    callback_view = InstagramOAuthCallback
    redirect_view = InstagramOAuthRedirect
    verbose_name = "Instagram Business"
    name = "instagram"

    authorization_url = "https://www.instagram.com/oauth/authorize"
    access_token_url = "https://api.instagram.com/oauth/access_token"  # nosec
    profile_url = "https://graph.instagram.com/v23.0/me?fields=user_id,username,name,account_type"

    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        # Instagram exposes no email address for the authenticated user
        return {
            "username": info.get("username"),
            "email": None,
            "name": info.get("name"),
        }
