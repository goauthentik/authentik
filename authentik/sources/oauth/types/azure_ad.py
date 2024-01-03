"""AzureAD OAuth2 Views"""
from typing import Any

from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class AzureADOAuthRedirect(OAuthRedirect):
    """Azure AD OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["openid", "https://graph.microsoft.com/User.Read"],
        }


class AzureADOAuthCallback(OpenIDConnectOAuth2Callback):
    """AzureAD OAuth2 Callback"""

    client_class = UserprofileHeaderAuthClient

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        mail = info.get("mail", None) or info.get("otherMails", [None])[0]
        return {
            "username": info.get("userPrincipalName"),
            "email": mail,
            "name": info.get("displayName"),
        }


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
    profile_url = "https://login.microsoftonline.com/common/openid/userinfo"
    oidc_well_known_url = (
        "https://login.microsoftonline.com/common/.well-known/openid-configuration"
    )
    oidc_jwks_url = "https://login.microsoftonline.com/common/discovery/keys"
