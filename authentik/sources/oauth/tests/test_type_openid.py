"""OpenID Type tests"""

from django.test import RequestFactory, TestCase
from jwt import encode
from requests_mock import Mocker

from authentik.core.tests.utils import create_test_cert
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback, OpenIDConnectType

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
        ak_context = OpenIDConnectType().get_base_user_properties(
            source=self.source, info=OPENID_USER
        )
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

    @Mocker()
    def test_userinfo_jwt(self, mock: Mocker):
        """Test userinfo API call"""
        jwks_cert = create_test_cert()
        self.source.profile_url = ""
        self.source.oidc_jwks = {"keys": [JWKSView.get_jwk_for_key(jwks_cert, "sig")]}
        self.source.save()
        token = generate_id()
        profile = (
            OpenIDConnectOAuth2Callback(request=self.factory.get("/"))
            .get_client(self.source)
            .get_profile_info(
                {
                    "token_type": "foo",
                    "access_token": token,
                    "id_token": encode(
                        {
                            "foo": "bar",
                        },
                        key=jwks_cert.private_key,
                        algorithm="RS256",
                        headers={"kid": self.source.oidc_jwks["keys"][0]["kid"]},
                    ),
                }
            )
        )
        self.assertEqual(
            profile,
            {
                "foo": "bar",
            },
        )
