"""WeChat Type tests"""

from django.test import RequestFactory, TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.wechat import WeChatType

WECHAT_USER = {
    "openid": "OPENID",
    "nickname": "NICKNAME",
    "sex": 1,
    "province": "PROVINCE",
    "city": "CITY",
    "country": "COUNTRY",
    "headimgurl": "https://thirdwx.qlogo.cn/mmopen/g3MonUZtNHkdmzicIlibx6iaFqAc56vxLSUfpb6n5WKSYVY0ChQKkiaJSgQ1dZuTOgvLLrhJbERQQ4eMsv84eavHiaiceqxibJxCfHe/0",
    "privilege": ["PRIVILEGE1", "PRIVILEGE2"],
    "unionid": " o6_buyCrymLUUFYHxvDU6M2PHl22",
}


class TestTypeWeChat(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="wechat",
        )
        self.factory = RequestFactory()

    def test_enroll_context(self):
        """Test WeChat Enrollment context"""
        ak_context = WeChatType().get_base_user_properties(
            source=self.source, info=WECHAT_USER, client=None, token={}
        )
        self.assertEqual(ak_context["username"], WECHAT_USER["unionid"])
        self.assertIsNone(ak_context["email"])
        self.assertEqual(ak_context["name"], WECHAT_USER["nickname"])
        self.assertEqual(ak_context["attributes"]["openid"], WECHAT_USER["openid"])
        self.assertEqual(ak_context["attributes"]["unionid"], WECHAT_USER["unionid"])

    def test_enroll_context_no_unionid(self):
        """Test WeChat Enrollment context without unionid"""
        user = WECHAT_USER.copy()
        del user["unionid"]
        ak_context = WeChatType().get_base_user_properties(
            source=self.source, info=user, client=None, token={}
        )
        self.assertEqual(ak_context["username"], WECHAT_USER["openid"])
        self.assertIsNone(ak_context["email"])
        self.assertEqual(ak_context["name"], WECHAT_USER["nickname"])
