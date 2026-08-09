"""Apple Type tests"""

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user
from jwt import decode

from authentik.core.tests.utils import RequestFactory, create_test_cert
from authentik.crypto.builder import PrivateKeyAlg
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.apple import AppleOAuthClient
from authentik.sources.oauth.types.registry import registry


class TestTypeApple(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.kp = create_test_cert(PrivateKeyAlg.ECDSA)
        self.team_id = generate_id()
        self.service_identifier = generate_id()
        self.key_id = generate_id()
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="apple",
            authorization_url="",
            profile_url="",
            consumer_key=f"{self.service_identifier};{self.team_id};{self.key_id}",
            consumer_secret=self.kp.key_data,
        )
        self.factory = RequestFactory()

    def test_login_challenge(self):
        """Test login_challenge"""
        request = self.factory.get("/")
        request.user = get_anonymous_user()

        oauth_type = registry.find_type("apple")
        challenge = oauth_type().login_challenge(self.source, request)
        self.assertTrue(challenge.is_valid(raise_exception=True))

    def test_client(self):
        """test client"""
        request = self.factory.get("/")
        request.user = get_anonymous_user()

        client = AppleOAuthClient(self.source, request)
        self.assertEqual(client.get_client_id(), self.service_identifier)
        self.assertIsNone(client.get_access_token_auth())

        args = client.get_access_token_args("foo", "bar")
        # client_secret will always change due to JWT issued with different time
        args.pop("client_secret")
        self.assertEqual(
            args,
            {
                "client_id": client.get_client_id(),
                "code": "bar",
                "grant_type": "authorization_code",
                "redirect_uri": "foo",
            },
        )

        secret_str = client.get_client_secret()
        secret = decode(
            secret_str,
            self.kp.private_key,
            algorithms=["ES256"],
            audience="https://appleid.apple.com",
        )
        self.assertEqual(secret["iss"], self.team_id)
        self.assertEqual(secret["sub"], self.service_identifier)
