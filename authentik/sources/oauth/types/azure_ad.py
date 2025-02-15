"""AzureAD OAuth2 Views"""

from typing import Any

from requests import RequestException
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
            "scope": [
                "openid",
                "https://graph.microsoft.com/User.Read",
                "https://graph.microsoft.com/GroupMember.Read.All",
            ],
        }


class AzureADClient(UserprofileHeaderAuthClient):
    """Fetch AzureAD group information"""

    def get_profile_info(self, token):
        profile_data = super().get_profile_info(token)
        group_response = self.session.request(
            "get",
            "https://graph.microsoft.com/v1.0/me/memberOf",
            headers={"Authorization": f"{token['token_type']} {token['access_token']}"},
        )
        try:
            group_response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning(
                "Unable to fetch user profile",
                exc=exc,
                response=exc.response.text if exc.response else str(exc),
            )
            return None
        profile_data["raw_groups"] = group_response.json()
        return profile_data


class AzureADOAuthCallback(OpenIDConnectOAuth2Callback):
    """AzureAD OAuth2 Callback"""

    client_class = AzureADClient

    def get_user_id(self, info: dict[str, str]) -> str:
        # Default try to get `id` for the Graph API endpoint
        # fallback to OpenID logic in case the profile URL was changed
        return info.get("id", super().get_user_id(info))


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

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        mail = info.get("mail", None) or info.get("otherMails", [None])[0]
        # Format group info
        groups = []
        group_id_dict = {}
        for group in info.get("raw_groups", {}).get("value", []):
            if group["@odata.type"] != "#microsoft.graph.group":
                continue
            groups.append(group["id"])
            group_id_dict[group["id"]] = group
        info["raw_groups"] = group_id_dict
        return {
            "username": info.get("userPrincipalName"),
            "email": mail,
            "name": info.get("displayName"),
            "groups": groups,
        }

    def get_base_group_properties(self, source, group_id, **kwargs):
        raw_group = kwargs["info"]["raw_groups"][group_id]
        return {
            "name": raw_group["displayName"],
        }
