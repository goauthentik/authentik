"""EntraID OAuth2 Views"""

from asyncio import run
from json import loads
from typing import Any

from httpx import HTTPError
from kiota_abstractions.api_error import APIError
from kiota_abstractions.authentication.anonymous_authentication_provider import (
    AnonymousAuthenticationProvider,
)
from kiota_abstractions.base_request_configuration import RequestConfiguration
from kiota_http.kiota_client_factory import KiotaClientFactory
from kiota_serialization_json.json_serialization_writer import JsonSerializationWriter
from msgraph.graph_request_adapter import GraphRequestAdapter, options
from msgraph.graph_service_client import GraphServiceClient
from msgraph_core import GraphClientFactory
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class EntraIDOAuthRedirect(OAuthRedirect):
    """Entra ID OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["openid", "https://graph.microsoft.com/User.Read"],
        }


class EntraIDClient(UserprofileHeaderAuthClient):
    """Fetch EntraID group information"""

    def get_profile_info(self, token):
        profile_data = super().get_profile_info(token)
        if "https://graph.microsoft.com/GroupMember.Read.All" not in self.source.additional_scopes:
            return profile_data
        try:
            profile_data["raw_groups"] = run(self.get_groups(token))
        except (APIError, HTTPError) as exc:
            LOGGER.warning("Unable to fetch user groups", exc=exc)
            return None
        return profile_data

    async def get_groups(self, token):
        """Fetch all memberships and retain Graph field names for property mappings."""
        config = RequestConfiguration()
        config.headers.add("Authorization", f"{token['token_type']} {token['access_token']}")
        async with GraphClientFactory.create_with_default_middleware(
            options=options, client=KiotaClientFactory.get_default_client()
        ) as http_client:
            client = GraphServiceClient(
                request_adapter=GraphRequestAdapter(AnonymousAuthenticationProvider(), http_client)
            )
            groups = []
            request = client.me.member_of
            while request:
                page = await request.get(config)
                groups.extend(page.value or [])
                request = (
                    client.me.member_of.with_url(page.odata_next_link)
                    if page.odata_next_link
                    else None
                )
        writer = JsonSerializationWriter()
        writer.write_collection_of_object_values("value", groups)
        return loads(writer.get_serialized_content())


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
        raw_groups = kwargs["info"]["raw_groups"]
        if group_id in raw_groups:
            name = raw_groups[group_id]["displayName"]
        else:
            name = group_id
        return {
            "name": name,
        }
