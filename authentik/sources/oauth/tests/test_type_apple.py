"""Apple Type tests"""

from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.common.tests import dummy_get_response
from authentik.crypto.generators import generate_id
from authentik.root.middleware import SessionMiddleware
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

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        oauth_type = registry.find_type("apple")
        challenge = oauth_type().login_challenge(self.source, request)
        self.assertTrue(challenge.is_valid(raise_exception=True))
