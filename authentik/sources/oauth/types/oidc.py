"""OpenID Connect OAuth Views"""

from typing import Any

from requests.auth import AuthBase, HTTPBasicAuth

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod, OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class OpenIDConnectOAuthRedirect(OAuthRedirect):
    """OpenIDConnect OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["openid", "email", "profile"],
        }


class OpenIDConnectClient(UserprofileHeaderAuthClient):
    def get_access_token_args(self, callback: str, code: str) -> dict[str, Any]:
        args = super().get_access_token_args(callback, code)
        if self.source.authorization_code_auth_method == AuthorizationCodeAuthMethod.POST_BODY:
            args["client_id"] = self.get_client_id()
            args["client_secret"] = self.get_client_secret()
        else:
            args.pop("client_id", None)
            args.pop("client_secret", None)
        return args

    def get_access_token_auth(self) -> AuthBase | None:
        if self.source.authorization_code_auth_method == AuthorizationCodeAuthMethod.BASIC_AUTH:
            return HTTPBasicAuth(self.get_client_id(), self.get_client_secret())
        return None


class OpenIDConnectOAuth2Callback(OAuthCallback):
    """OpenIDConnect OAuth2 Callback"""

    client_class = OpenIDConnectClient

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("sub", None)


@registry.register()
class OpenIDConnectType(SourceType):
    """OpenIDConnect Type definition"""

    callback_view = OpenIDConnectOAuth2Callback
    redirect_view = OpenIDConnectOAuthRedirect
    verbose_name = "OpenID Connect"
    name = "openidconnect"

    urls_customizable = True

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("nickname", info.get("preferred_username")),
            "email": info.get("email"),
            "name": info.get("name"),
            "groups": info.get("groups", []),
        }
