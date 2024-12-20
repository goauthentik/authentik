"""Mailcow OAuth Views"""

from typing import Any

from requests.exceptions import RequestException
from structlog.stdlib import get_logger

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

LOGGER = get_logger()


class MailcowOAuthRedirect(OAuthRedirect):
    """Mailcow OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": ["profile"],
        }


class MailcowOAuth2Client(OAuth2Client):
    """MailcowOAuth2Client, for some reason, mailcow does not like the default headers"""

    def get_profile_info(self, token: dict[str, str]) -> dict[str, Any] | None:
        "Fetch user profile information."
        profile_url = self.source.source_type.profile_url or ""
        if self.source.source_type.urls_customizable and self.source.profile_url:
            profile_url = self.source.profile_url
        response = self.session.request(
            "get",
            f"{profile_url}?access_token={token['access_token']}",
        )
        try:
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning("Unable to fetch user profile", exc=exc, body=response.text)
            return None
        return response.json()


class MailcowOAuth2Callback(OAuthCallback):
    """Mailcow OAuth2 Callback"""

    client_class = MailcowOAuth2Client


@registry.register()
class MailcowType(SourceType):
    """Mailcow Type definition"""

    callback_view = MailcowOAuth2Callback
    redirect_view = MailcowOAuthRedirect
    verbose_name = "Mailcow"
    name = "mailcow"

    urls_customizable = True

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        return {
            "username": info.get("full_name"),
            "email": info.get("email"),
            "name": info.get("full_name"),
        }
