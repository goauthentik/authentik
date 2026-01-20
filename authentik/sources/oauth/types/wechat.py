"""WeChat (Weixin) OAuth Views"""

from typing import Any

from requests.exceptions import RequestException

from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import SourceType, registry
from authentik.sources.oauth.views.callback import OAuthCallback
from authentik.sources.oauth.views.redirect import OAuthRedirect


class WeChatOAuthRedirect(OAuthRedirect):
    """WeChat OAuth2 Redirect"""

    def get_additional_parameters(self, source: OAuthSource):  # pragma: no cover
        # WeChat (Weixin) for Websites official documentation requires 'snsapi_login'
        # as the *only* scope for the QR code-based login flow.
        # Ref: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html (Step 1)  # noqa: E501
        return {
            "scope": ["snsapi_login"],
        }


class WeChatOAuth2Client(OAuth2Client):
    """
    WeChat OAuth2 Client

    Handles the non-standard parts of the WeChat OAuth2 flow.
    """

    def get_access_token(self, redirect_uri: str, code: str) -> dict[str, Any]:
        """
        Get access token from WeChat.

        WeChat uses a non-standard GET request for the token exchange,
        unlike the standard OAuth2 POST request. The AppID (client_id)
        and AppSecret (client_secret) are passed as URL query parameters.
        """
        token_url = self.get_access_token_url()
        params = {
            "appid": self.get_client_id(),
            "secret": self.get_client_secret(),
            "code": code,
            "grant_type": "authorization_code",
        }

        # Send the GET request using the base class's session handler
        response = self.do_request("get", token_url, params=params)

        try:
            response.raise_for_status()
        except RequestException as exc:
            self.logger.warning("Unable to fetch wechat token", exc=exc)
            raise exc

        data = response.json()

        # Handle WeChat's specific error format (JSON with 'errcode' and 'errmsg')
        if "errcode" in data:
            self.logger.warning(
                "Unable to fetch wechat token",
                errcode=data.get("errcode"),
                errmsg=data.get("errmsg"),
            )
            raise RequestException(data.get("errmsg"))

        return data

    def get_profile_info(self, token: dict[str, Any]) -> dict[str, Any]:
        """
        Get Userinfo from WeChat.

        This API call requires both the 'access_token' and the 'openid'
        (which was returned during the token exchange).
        """
        profile_url = self.get_profile_url()
        params = {
            "access_token": token.get("access_token"),
            "openid": token.get("openid"),
            "lang": "en",  # or 'zh_CN' (Simplified Chinese), 'zh_TW' (Traditional)
        }

        response = self.do_request("get", profile_url, params=params)

        try:
            response.raise_for_status()
        except RequestException as exc:
            self.logger.warning("Unable to fetch wechat userinfo", exc=exc)
            raise exc

        data = response.json()

        # Handle WeChat's specific error format
        if "errcode" in data:
            self.logger.warning(
                "Unable to fetch wechat userinfo",
                errcode=data.get("errcode"),
                errmsg=data.get("errmsg"),
            )
            raise RequestException(data.get("errmsg"))

        return data


class WeChatOAuth2Callback(OAuthCallback):
    """WeChat OAuth2 Callback"""

    # Specify our custom Client to handle the non-standard WeChat flow
    client_class = WeChatOAuth2Client


@registry.register()
class WeChatType(SourceType):
    """WeChat Type definition"""

    callback_view = WeChatOAuth2Callback
    redirect_view = WeChatOAuthRedirect
    verbose_name = "WeChat"
    name = "wechat"

    # WeChat API URLs are fixed and not customizable
    urls_customizable = False

    # URLs for the WeChat "Login for Websites" authorization flow
    authorization_url = "https://open.weixin.qq.com/connect/qrconnect"
    # This is a public URL, not a hardcoded secret
    access_token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"  # nosec B105
    profile_url = "https://api.weixin.qq.com/sns/userinfo"

    # Note: 'authorization_code_auth_method' is intentionally omitted.
    # The base OAuth2Client defaults to POST_BODY, but our custom
    # WeChatOAuth2Client overrides get_access_token() to use GET,
    # so this setting would be misleading.

    def get_base_user_properties(self, info: dict[str, Any], **kwargs) -> dict[str, Any]:
        """
        Map WeChat userinfo to authentik user properties.
        """
        # The WeChat userinfo API (sns/userinfo) does *not* return an email address.
        # We explicitly set 'email' to None. Authentik will typically
        # prompt the user to provide one on their first login if it's required.

        # 'unionid' is the preferred unique identifier as it's consistent
        # across multiple apps under the same WeChat Open Platform account.
        # 'openid' is the fallback, which is only unique to this specific AppID.
        return {
            "username": info.get("unionid", info.get("openid")),
            "email": None,  # WeChat API does not provide Email
            "name": info.get("nickname"),
            "attributes": {
                # Save all other relevant info as user attributes
                "headimgurl": info.get("headimgurl"),
                "sex": info.get("sex"),
                "city": info.get("city"),
                "province": info.get("province"),
                "country": info.get("country"),
                "unionid": info.get("unionid"),
                "openid": info.get("openid"),
            },
        }
