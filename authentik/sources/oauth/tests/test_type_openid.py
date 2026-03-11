"""OpenID Type tests"""

import time

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
        """Test id_token fallback when profile_url is empty"""
        jwks_cert = create_test_cert()
        client_id = generate_id()
        self.source.profile_url = ""
        self.source.consumer_key = client_id
        self.source.oidc_jwks = {"keys": [JWKSView.get_jwk_for_key(jwks_cert, "sig")]}
        self.source.save()
        token = generate_id()
        now = int(time.time())
        id_token_payload = {
            "iss": "https://example.com",
            "sub": OPENID_USER["sub"],
            "aud": client_id,
            "exp": now + 3600,
            "iat": now,
            "name": OPENID_USER["name"],
            "email": OPENID_USER["email"],
            "nickname": OPENID_USER["nickname"],
        }
        profile = (
            OpenIDConnectOAuth2Callback(request=self.factory.get("/"))
            .get_client(self.source)
            .get_profile_info(
                {
                    "token_type": "Bearer",
                    "access_token": token,
                    "id_token": encode(
                        id_token_payload,
                        key=jwks_cert.private_key,
                        algorithm="RS256",
                        headers={"kid": self.source.oidc_jwks["keys"][0]["kid"]},
                    ),
                }
            )
        )
        self.assertEqual(profile["sub"], OPENID_USER["sub"])
        self.assertEqual(profile["name"], OPENID_USER["name"])
        self.assertEqual(profile["email"], OPENID_USER["email"])
        self.assertEqual(profile["aud"], client_id)
        self.assertEqual(profile["iss"], "https://example.com")
