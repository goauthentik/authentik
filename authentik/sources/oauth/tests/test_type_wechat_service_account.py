"""WeChat Service Account Type tests"""

from unittest.mock import MagicMock, patch
from urllib.parse import parse_qsl, urlparse

from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource, WeChatServiceAccountOAuthSource
from authentik.sources.oauth.types.registry import registry
from authentik.sources.oauth.types.wechat_service_account import (
    WeChatServiceAccountOAuth2Client,
    WeChatServiceAccountType,
)

WECHAT_USER = {
    "openid": "OPENID",
    "nickname": "NICKNAME",
    "sex": 1,
    "province": "PROVINCE",
    "city": "CITY",
    "country": "COUNTRY",
    "headimgurl": "https://thirdwx.qlogo.cn/mmopen/g3MonUZtNHkdmzicIlibx6iaFqAc56vxLSUfpb6n5WKSYVY0ChQKkiaJSgQ1dZuTOgvLLrhJbERQQ4eMsv84eavHiaiceqxibJxCfHe/0",
    "privilege": ["PRIVILEGE1", "PRIVILEGE2"],
    "unionid": "o6_buyCrymLUUFYHxvDU6M2PHl22",
}


class TestTypeWeChatServiceAccount(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.appid = generate_id()
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="wechatserviceaccount",
            consumer_key=self.appid,
        )
        self.factory = RequestFactory()

    def _client(self) -> WeChatServiceAccountOAuth2Client:
        request = self.factory.get("/")
        request.session = {}
        request.user = get_anonymous_user()
        return WeChatServiceAccountOAuth2Client(self.source, request, callback="/callback")

    def test_registered(self):
        """Test the type is registered under its own name"""
        self.assertIs(registry.find_type("wechatserviceaccount"), WeChatServiceAccountType)
        self.assertIsNot(registry.find_type("wechat"), WeChatServiceAccountType)

    def test_model_name_matches_type_name(self):
        """Both the admin interface and OAuthSource.icon_url derive the provider
        type by stripping `oauthsource` off the model name, so the two must agree
        or the source silently falls back to the default type"""
        model_name = WeChatServiceAccountOAuthSource._meta.model_name
        self.assertEqual(
            model_name.replace(OAuthSource._meta.model_name, ""),
            WeChatServiceAccountType.name,
        )

    def test_redirect_url(self):
        """Test the authorization URL matches the documented web authorization form"""
        url = self._client().get_redirect_url({"scope": ["snsapi_userinfo"]})
        parsed = urlparse(url)
        self.assertEqual(parsed.netloc, "open.weixin.qq.com")
        self.assertEqual(parsed.path, "/connect/oauth2/authorize")
        # WeChat requires the fragment to be present and last
        self.assertEqual(parsed.fragment, "wechat_redirect")
        # Documented order:
        # appid, redirect_uri, response_type, scope, state
        args = parse_qsl(parsed.query)
        self.assertEqual(
            [key for key, _ in args],
            ["appid", "redirect_uri", "response_type", "scope", "state"],
        )
        self.assertEqual(dict(args)["appid"], self.appid)
        self.assertEqual(dict(args)["scope"], "snsapi_userinfo")

    def test_enroll_context(self):
        """Test WeChat Service Account enrollment context"""
        ak_context = WeChatServiceAccountType().get_base_user_properties(
            source=self.source, info=WECHAT_USER, client=None, token={}
        )
        self.assertEqual(ak_context["username"], WECHAT_USER["unionid"])
        self.assertIsNone(ak_context["email"])
        self.assertEqual(ak_context["name"], WECHAT_USER["nickname"])
        self.assertEqual(ak_context["attributes"]["openid"], WECHAT_USER["openid"])
        self.assertEqual(ak_context["attributes"]["unionid"], WECHAT_USER["unionid"])

    def test_enroll_context_no_unionid(self):
        """Test WeChat Service Account enrollment context without unionid"""
        user = WECHAT_USER.copy()
        del user["unionid"]
        ak_context = WeChatServiceAccountType().get_base_user_properties(
            source=self.source, info=user, client=None, token={}
        )
        self.assertEqual(ak_context["username"], WECHAT_USER["openid"])
        self.assertIsNone(ak_context["email"])

    def test_profile_info_falls_back_to_token(self):
        """unionid is only present in the token response when the account is
        bound to an Open Platform account, and must not be lost"""
        userinfo = WECHAT_USER.copy()
        del userinfo["unionid"]
        response = MagicMock()
        response.json.return_value = userinfo
        with patch.object(WeChatServiceAccountOAuth2Client, "do_request", return_value=response):
            profile = self._client().get_profile_info(
                {"access_token": "AT", "openid": "OPENID", "unionid": "UNIONID"}
            )
        self.assertEqual(profile["unionid"], "UNIONID")
        self.assertEqual(
            WeChatServiceAccountType().get_base_user_properties(
                source=self.source, info=profile, client=None, token={}
            )["username"],
            "UNIONID",
        )

    def test_profile_info_prefers_userinfo(self):
        """The userinfo response wins over the token when both carry a unionid"""
        response = MagicMock()
        response.json.return_value = WECHAT_USER.copy()
        with patch.object(WeChatServiceAccountOAuth2Client, "do_request", return_value=response):
            profile = self._client().get_profile_info(
                {"access_token": "AT", "openid": "OPENID", "unionid": "OTHER"}
            )
        self.assertEqual(profile["unionid"], WECHAT_USER["unionid"])

    def test_profile_info_error(self):
        """WeChat reports errors with a 200 response and an errcode field"""
        response = MagicMock()
        response.json.return_value = {"errcode": 40003, "errmsg": "invalid openid"}
        with patch.object(WeChatServiceAccountOAuth2Client, "do_request", return_value=response):
            self.assertIsNone(self._client().get_profile_info({"access_token": "AT"}))
