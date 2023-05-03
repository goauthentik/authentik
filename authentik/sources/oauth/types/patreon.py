"""Patreon OAuth Views"""
from typing import Any

from authentik.sources.oauth.clients.oauth2 import UserprofileHeaderAuthClient
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class PatreonOAuthRedirect(OAuthRedirect):
    """Patreon OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["openid", "email", "profile"],
        }


class PatreonOAuthCallback(OAuthCallback):
    """Patreon OAuth2 Callback"""

    client_class: UserprofileHeaderAuthClient

    def get_user_id(self, info: dict[str, str]) -> str:
        return info.get("data", {}).get("id")

    def get_user_enroll_context(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "username": info.get("data", {}).get("attributes", {}).get("vanity"),
            "email": info.get("data", {}).get("attributes", {}).get("email"),
            "name": info.get("data", {}).get("attributes", {}).get("full_name"),
        }


@registry.register()
class PatreonType(SourceType):
    """OpenIDConnect Type definition"""

    callback_view = PatreonOAuthCallback
    redirect_view = PatreonOAuthRedirect
    name = "Patreon"
    slug = "patreon"

    authorization_url = "https://www.patreon.com/oauth2/authorize"
    access_token_url = "https://www.patreon.com/api/oauth2/token"  # nosec
    profile_url = "https://www.patreon.com/api/oauth2/api/current_user"
