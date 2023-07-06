"""OpenID Type tests"""
from django.test import RequestFactory, TestCase
from requests_mock import Mocker

from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback

# https://connect2id.com/products/server/docs/api/userinfo
OPENID_USER = {
    "sub": "83692",
    "name": "Alice Adams",
    "email": "alice@example.com",
    "department": "Engineering",
    "birthdate": "1975-12-31",
    "nickname": "foo",
}


class TestTypeOpenID(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="http://localhost/userinfo",
            consumer_key="",
        )
        self.factory = RequestFactory()

    def test_enroll_context(self):
        """Test OpenID Enrollment context"""
        ak_context = OpenIDConnectOAuth2Callback().get_user_enroll_context(OPENID_USER)
        self.assertEqual(ak_context["username"], OPENID_USER["nickname"])
        self.assertEqual(ak_context["email"], OPENID_USER["email"])
        self.assertEqual(ak_context["name"], OPENID_USER["name"])

    @Mocker()
    def test_userinfo(self, mock: Mocker):
        """Test userinfo API call"""
        mock.get("http://localhost/userinfo", json=OPENID_USER)
        token = generate_id()
        OpenIDConnectOAuth2Callback(request=self.factory.get("/")).get_client(
            self.source
        ).get_profile_info(
            {
                "token_type": "foo",
                "access_token": token,
            }
        )
        self.assertEqual(mock.last_request.query, "")
        self.assertEqual(mock.last_request.headers["Authorization"], f"foo {token}")
