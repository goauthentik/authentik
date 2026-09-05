"""TikTok OAuth Views"""

from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlparse, urlunparse

from requests.exceptions import RequestException

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod, OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect

# Fields requestable with the `user.info.basic` scope. Anything beyond this set
# requires additional scopes which are only granted to reviewed applications.
# Ref: https://developers.tiktok.com/doc/tiktok-api-v2-get-user-info
USER_INFO_FIELDS = "open_id,union_id,display_name,avatar_url"


class TikTokOAuth2Client(OAuth2Client):
    """
    TikTok OAuth2 Client

    Handles the non-standard parts of the TikTok Login Kit flow: TikTok names the
    client identifier `client_key` rather than `client_id`, separates scopes with
    commas rather than spaces, and nests the userinfo payload under `data.user`.
    """

    def get_redirect_args(self) -> dict[str, str]:
        """Get request parameters for redirect url.

        TikTok expects `client_key` where RFC 6749 specifies `client_id`.
        """
        args = super().get_redirect_args()
        args["client_key"] = args.pop("client_id")
        return args

    def get_redirect_url(self, parameters=None) -> str:
        """Build authentication redirect url.

        The base client joins scopes with spaces per RFC 6749 section 3.3, but
        TikTok requires a comma-separated list.
        """
        url = super().get_redirect_url(parameters)
        parsed_url = urlparse(url)
        args = parse_qs(parsed_url.query)
        if "scope" in args:
            args["scope"] = [",".join(args["scope"][0].split(" "))]
        return urlunparse(parsed_url._replace(query=urlencode(args, quote_via=quote, doseq=True)))

    def get_access_token_args(self, callback: str | None, code: str | None) -> dict[str, Any]:
        """Get parameters for the token exchange.

        As with the authorization request, TikTok expects `client_key`.
        """
        args = super().get_access_token_args(callback, code)
        args["client_key"] = args.pop("client_id")
        return args

    def get_profile_info(self, token: dict[str, str]) -> dict[str, Any] | None:
        """Get Userinfo from TikTok.

        The endpoint requires an explicit `fields` parameter and returns the user
        object nested under `data.user`, with a status object under `error`.
        """
        profile_url = self.source.source_type.profile_url or ""
        try:
            response = self.do_request(
                "get",
                profile_url,
                params={"fields": USER_INFO_FIELDS},
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )
            response.raise_for_status()
        except RequestException as exc:
            self.logger.warning(
                "Unable to fetch tiktok user info",
                exc=exc,
                response=exc.response.text if exc.response is not None else str(exc),
            )
            return None
        data = response.json()
        # TikTok signals failure in the body with a non-"ok" error code, even on HTTP 200
        error = data.get("error", {})
        if error.get("code", "ok") != "ok":
            self.logger.warning(
                "Unable to fetch tiktok user info",
                code=error.get("code"),
                message=error.get("message"),
            )
            return None
        return data.get("data", {}).get("user")


class TikTokOAuthRedirect(OAuthRedirect):
    """TikTok OAuth2 Redirect"""

    client_class = TikTokOAuth2Client

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        return {
            "scope": ["user.info.basic"],
        }


class TikTokOAuth2Callback(OAuthCallback):
    """TikTok OAuth2 Callback"""

    client_class = TikTokOAuth2Client

    def get_user_id(self, info: dict[str, Any]) -> str | None:
        return info.get("union_id", info.get("open_id"))


@registry.register()
class TikTokType(SourceType):
    """TikTok Type definition"""

    callback_view = TikTokOAuth2Callback
    redirect_view = TikTokOAuthRedirect
    verbose_name = "TikTok"
    name = "tiktok"

    urls_customizable = False

    authorization_url = "https://www.tiktok.com/v2/auth/authorize/"
    access_token_url = "https://open.tiktokapis.com/v2/oauth/token/"  # nosec B105
    profile_url = "https://open.tiktokapis.com/v2/user/info/"

    # TikTok takes the client credentials in the token request body rather than
    # via HTTP Basic auth; TikTokOAuth2Client then renames client_id to client_key.
    authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Map TikTok userinfo to authentik user properties."""
        # TikTok does not expose an email address through any scope, so email is
        # left unset and must be collected during enrollment if it is required.
        # `union_id` is stable across all apps owned by the same developer;
        # `open_id` is only unique within a single app, and is the fallback.
        return {
            "username": info.get("union_id", info.get("open_id")),
            "email": None,
            "name": info.get("display_name"),
            "attributes": {
                "avatar_url": info.get("avatar_url"),
                "open_id": info.get("open_id"),
                "union_id": info.get("union_id"),
            },
        }
