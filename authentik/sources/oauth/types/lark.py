"""Lark (Feishu) OAuth Views"""

from typing import Any

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger
from requests.exceptions import RequestException


class LarkOAuthRedirect(OAuthRedirect):
    """Lark OAuth2 Redirect"""

    def get_additional_parameters(self, source):  # pragma: no cover
        return {
            "scope": [
                "contact:user.phone:readonly",
                "contact:user.employee_id:readonly",
                "contact:user.email:readonly",
            ],
        }


class LarkOAuth2Client(OAuth2Client):
    """Lark OAuth2 Client"""

    def get_access_token(self, **request_kwargs) -> dict[str, Any] | None:

        LOGGER = get_logger()

        callback = self.request.build_absolute_uri(self.callback or self.request.path)
        if not self.check_application_state():
            LOGGER.warning("Application state check failed.")
            return {"error": "State check failed."}
        code = self.get_request_arg("code", None)
        if not code:
            LOGGER.warning("No code returned by the source")
            error = self.get_request_arg("error", None)
            error_desc = self.get_request_arg("error_description", None)
            return {"error": error_desc or error or _("No token received.")}

        """Add client_id and client_secret to body."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.get_client_id(),
            "client_secret": self.get_client_secret(),
            "redirect_uri": callback,
        }

        try:
            access_token_url = self.source.source_type.access_token_url or ""
            if self.source.source_type.urls_customizable and self.source.access_token_url:
                access_token_url = self.source.access_token_url

            """Not using parent class"""
            response = self.session.request(
                "post", access_token_url, data=data, headers=self._default_headers, **request_kwargs
            )
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.warning(
                "Unable to fetch access token",
                exc=exc,
                response=exc.response.text if exc.response else str(exc),
            )
            return None

        return response.json()


class LarkOAuth2Callback(OAuthCallback):
    """Lark OAuth2 Callback"""

    client_class = LarkOAuth2Client

    def get_user_id(self, info: dict[str, str]) -> str:
        user_data = info.get("data", {})
        """Get unique identifier from user info."""
        user_id = user_data.get("open_id")
        return user_id


@registry.register()
class LarkType(SourceType):
    """Lark Type definition"""

    callback_view = LarkOAuth2Callback
    redirect_view = LarkOAuthRedirect
    verbose_name = "Lark"
    name = "lark"

    urls_customizable = True

    authorization_url = "https://open.feishu.cn/open-apis/authen/v1/authorize"
    access_token_url = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    profile_url = "https://open.feishu.cn/open-apis/authen/v1/user_info"

    def get_base_user_properties(
        self,
        info: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        info = info.get("data", {})
        return {
            "username": info.get("open_id"),
            "email": info.get("email"),
            "name": info.get("name"),
            "avatar": info.get("avatar_url"),
            "mobile": info.get("mobile"),
        }
