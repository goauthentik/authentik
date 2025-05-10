from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.crypto.generators import generate_id
from authentik.sources.oauth.clients.oauth2 import OAuth2Client
from authentik.sources.oauth.models import AuthorizationCodeAuthMethod, OAuthSource
from authentik.sources.oauth.types.oidc import OpenIDConnectClient


class TestOAuthClient(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key=generate_id(),
        )
        self.factory = RequestFactory()

    def test_client_post_body_auth(self):
        """Test login_challenge"""
        self.source.provider_type = "apple"
        self.source.save()
        request = self.factory.get("/")
        request.session = {}
        request.user = get_anonymous_user()
        client = OAuth2Client(self.source, request)
        self.assertIsNone(client.get_access_token_auth())
        args = client.get_access_token_args("", "")
        self.assertIn("client_id", args)
        self.assertIn("client_secret", args)

    def test_client_basic_auth(self):
        """Test login_challenge"""
        self.source.provider_type = "reddit"
        self.source.save()
        request = self.factory.get("/")
        request.session = {}
        request.user = get_anonymous_user()
        client = OAuth2Client(self.source, request)
        self.assertIsNotNone(client.get_access_token_auth())
        args = client.get_access_token_args("", "")
        self.assertNotIn("client_id", args)
        self.assertNotIn("client_secret", args)

    def test_client_openid_auth(self):
        """Test login_challenge"""
        request = self.factory.get("/")
        request.session = {}
        request.user = get_anonymous_user()
        client = OpenIDConnectClient(self.source, request)

        self.assertIsNotNone(client.get_access_token_auth())
        args = client.get_access_token_args("", "")
        self.assertNotIn("client_id", args)
        self.assertNotIn("client_secret", args)

        self.source.authorization_code_auth_method = AuthorizationCodeAuthMethod.POST_BODY
        self.source.save()
        client = OpenIDConnectClient(self.source, request)

        self.assertIsNone(client.get_access_token_auth())
        args = client.get_access_token_args("", "")
        self.assertIn("client_id", args)
        self.assertIn("client_secret", args)
