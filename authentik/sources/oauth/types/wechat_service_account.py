"""WeChat Service Account (Weixin 服务号) OAuth Views"""

from typing import Any

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import registry
from authentik.sources.oauth.types.wechat import (
    WeChatOAuth2Callback,
    WeChatOAuth2Client,
    WeChatType,
)
from authentik.sources.oauth.views.redirect import OAuthRedirect


class WeChatServiceAccountOAuth2Client(WeChatOAuth2Client):
    """
    WeChat Service Account OAuth2 Client.

    The token and userinfo endpoints are identical to the "WeChat for Websites"
    flow, so all of the non-standard handling (GET token exchange, ``errcode``
    error format) is inherited. Only the authorization request differs.
    """

    def get_redirect_args(self) -> dict[str, str]:
        """
        Build the authorization parameters in the order WeChat documents.

        The base class appends ``appid`` last because it renames ``client_id``
        via ``pop()``. ``scope`` is seeded here so that the value injected by
        :class:`WeChatServiceAccountOAuthRedirect` replaces it in place rather than being
        appended after ``state``, which yields the exact parameter sequence
        from the web authorization documentation.
        """
        args = super().get_redirect_args()
        return {
            "appid": args.pop("appid"),
            "redirect_uri": args.pop("redirect_uri"),
            "response_type": args.pop("response_type"),
            "scope": "",
            **args,
        }

    def get_profile_info(self, token: dict[str, Any]) -> dict[str, Any] | None:
        """
        Get Userinfo from WeChat.

        Unlike the website flow, the web authorization token response already
        carries ``openid`` and ``unionid``. They are merged in as a fallback so
        that a user resolves to the same authentik account regardless of which
        WeChat source they came through, as long as both applications belong to
        the same Open Platform account.
        """
        profile = super().get_profile_info(token)
        if profile is None:
            return None
        for key in ("openid", "unionid"):
            if token.get(key):
                profile.setdefault(key, token[key])
        return profile


class WeChatServiceAccountOAuthRedirect(OAuthRedirect):
    """WeChat Service Account OAuth2 Redirect"""

    client_class = WeChatServiceAccountOAuth2Client

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        # `snsapi_userinfo` prompts the user for consent and returns their
        # profile. The silent `snsapi_base` scope is not usable here: it only
        # yields an openid and makes the userinfo endpoint reject the request.
        return {
            "scope": ["snsapi_userinfo"],
        }


class WeChatServiceAccountOAuth2Callback(WeChatOAuth2Callback):
    """WeChat Service Account OAuth2 Callback"""

    client_class = WeChatServiceAccountOAuth2Client


@registry.register()
class WeChatServiceAccountType(WeChatType):
    """
    WeChat Service Account Type definition.

    WeChat only grants web authorization to verified Service Accounts; the
    other account types, including Subscription Accounts (which WeChat's
    documentation now calls 公众号), cannot use this flow.
    """

    callback_view = WeChatServiceAccountOAuth2Callback
    redirect_view = WeChatServiceAccountOAuthRedirect
    verbose_name = "WeChat Service Account"
    name = "wechatserviceaccount"

    urls_customizable = False

    # URLs for the WeChat Service Account "web authorization" flow. The
    # `#wechat_redirect` fragment is required by WeChat and is preserved by
    # BaseOAuthClient.get_redirect_url(), which only replaces the query string.
    authorization_url = "https://open.weixin.qq.com/connect/oauth2/authorize#wechat_redirect"
    # This is a public URL, not a hardcoded secret
    access_token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"  # nosec B105
    profile_url = "https://api.weixin.qq.com/sns/userinfo"
