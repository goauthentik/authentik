"""EntraID OAuth2 Views"""

from typing import Any
from urllib.parse import urlparse, urlunparse
from requests import RequestException
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()

def get_graph_base_url(profile_url: str) -> str:
    """Dynamically get the graph base URL from the full profile URL."""
    parsed_url = urlparse(profile_url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, "", "", "", ""))


def get_graph_scope(profile_url: str, permission: str) -> str:
    """Dynamically build a full graph scope from the profile URL."""
    base_url = get_graph_base_url(profile_url)
    return f"{base_url}/{permission}"

class EntraIDOAuthRedirect(OAuthRedirect):
    """Entra ID OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["openid", get_graph_scope(source.profile_url, "User.Read")],
        }


class EntraIDClient(UserprofileHeaderAuthClient):
    """Fetch EntraID group information"""

    def get_profile_info(self, token):
        profile_data = super().get_profile_info(token)
        group_read_scope = get_graph_scope(self.source.profile_url, "GroupMember.Read.All")

        # Check if group reading scope is configured (with fallback for different scope formats)
        if group_read_scope not in self.source.additional_scopes:
            # Try alternative scope names that might be configured
            alternative_scopes = [
                "GroupMember.Read.All",
                "Group.Read.All", 
                f"{get_graph_base_url(self.source.profile_url)}/Group.Read.All"
            ]
            
            scope_found = False
            for alt_scope in alternative_scopes:
                if alt_scope in self.source.additional_scopes:
                    scope_found = True
                    break
            
            if not scope_found:
                return profile_data

        # Build the memberOf URL using the same base as profile_url
        graph_base_url = get_graph_base_url(self.source.profile_url)
        member_of_url = f"{graph_base_url}/v1.0/me/memberOf"
        group_response = self.session.request(
            "get",
            member_of_url,
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


class EntraIDOAuthCallback(OpenIDConnectOAuth2Callback):
    """EntraID OAuth2 Callback"""

    client_class = EntraIDClient

    def get_user_id(self, info: dict[str, str]) -> str:
        # Default try to get `id` for the Graph API endpoint
        # fallback to OpenID logic in case the profile URL was changed
        return info.get("id", super().get_user_id(info))


@registry.register()
class EntraIDType(SourceType):
    """Entra ID Type definition"""

    callback_view = EntraIDOAuthCallback
    redirect_view = EntraIDOAuthRedirect
    verbose_name = "Entra ID"
    name = "entraid"

    urls_customizable = True

    authorization_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    access_token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"  # nosec
    profile_url = "https://graph.microsoft.com/v1.0/me"
    oidc_jwks_url = "https://login.microsoftonline.com/common/discovery/keys"

    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        mail = info.get("mail", None) or info.get("email", None) or info.get("userPrincipalName", None) or info.get("otherMails", [None])[0]
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
