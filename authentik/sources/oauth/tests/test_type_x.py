"""X Type tests"""

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.x import XType

# https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-me
X_USER = {"data": {"id": "2244994945", "name": "XDev", "username": "X Dev"}}


class TestTypeX(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test X Enrollment context"""
        ak_context = XType().get_base_user_properties(source=self.source, info=X_USER)
        self.assertEqual(ak_context["username"], X_USER["data"]["username"])
        self.assertEqual(ak_context["email"], None)
        self.assertEqual(ak_context["name"], X_USER["data"]["name"])
