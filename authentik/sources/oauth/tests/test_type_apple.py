"""Apple Type tests"""

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.core.tests.utils import RequestFactory
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.registry import registry


class TestTypeApple(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="apple",
            authorization_url="",
            profile_url="",
            consumer_key=generate_id(),
        )
        self.factory = RequestFactory()

    def test_login_challenge(self):
        """Test login_challenge"""
        request = self.factory.get("/")
        request.user = get_anonymous_user()

        oauth_type = registry.find_type("apple")
        challenge = oauth_type().login_challenge(self.source, request)
        self.assertTrue(challenge.is_valid(raise_exception=True))
