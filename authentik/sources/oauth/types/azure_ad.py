"""AzureAD OAuth2 Views"""

from typing import Any

import jwt
from django.http import HttpRequest
from django.utils.crypto import get_random_string
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class AzureADOAuthClient(UserprofileHeaderAuthClient):
    def __init__(self, source: OAuthSource, request: HttpRequest, callback: str | None = None):
        super().__init__(source, request, callback)
        self.jwks = jwt.PyJWKClient(self.source.oidc_jwks_url)
        self.nonce = None

    def get_redirect_args(self) -> dict[str, str]:
        args = super().get_redirect_args()
        args["response_type"] = args.get("response_type", "code") + " id_token"
        args["response_mode"] = "form_post"
        args["nonce"] = get_random_string(48)
        self.request.session[self.nonce_key] = args["nonce"]
        return args

    def get_access_token(self, **request_kwargs) -> dict[str, Any] | None:
        token = super().get_access_token(**request_kwargs)
        if token is None:
            return None
        self.logger.info("Query", query=self.request.POST)
        token["id_token"] = self.request.POST.get("id_token")
        return token

    def get_profile_info(self, token: dict[str, str]) -> dict[str, Any] | None:
        self.logger.info("ID Token", id_token=token["id_token"])
        return jwt.decode(token["id_token"].encode(), )

    @property
    def nonce_key(self):
        return f"{self.session_key}-nonce"


class AzureADOAuthRedirect(OAuthRedirect):
    """Azure AD OAuth2 Redirect"""
    client_class = AzureADOAuthClient

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["openid"],
        }


class AzureADOAuthCallback(OpenIDConnectOAuth2Callback):
    """AzureAD OAuth2 Callback"""

    client_class = AzureADOAuthClient

    # def get_user_id(self, info: dict[str, str]) -> str:
    #     # Default try to get `id` for the Graph API endpoint
    #     # fallback to OpenID logic in case the profile URL was changed
    #     return info.get("id", super().get_user_id(info))

    # def get_user_enroll_context(
    #     self,
    #     info: dict[str, Any],
    # ) -> dict[str, Any]:
    #     mail = info.get("mail", None) or info.get("otherMails", [None])[0]
    #     return {
    #         "username": info.get("userPrincipalName"),
    #         "email": mail,
    #         "name": info.get("displayName"),
    #     }


@registry.register()
class AzureADType(SourceType):
    """Azure AD Type definition"""

    callback_view = AzureADOAuthCallback
    redirect_view = AzureADOAuthRedirect
    verbose_name = "Azure AD"
    name = "azuread"

    urls_customizable = True

    authorization_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    access_token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"  # nosec
    profile_url = "https://graph.microsoft.com/v1.0/me"
    oidc_well_known_url = (
        "https://login.microsoftonline.com/common/.well-known/openid-configuration"
    )
    oidc_jwks_url = "https://login.microsoftonline.com/common/discovery/keys"
