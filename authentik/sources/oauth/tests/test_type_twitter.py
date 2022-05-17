"""Twitter Type tests"""
from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.twitter import TwitterOAuthCallback

# https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-me
TWITTER_USER = {"data": {"id": "2244994945", "name": "TwitterDev", "username": "Twitter Dev"}}


class TestTypeGitHub(TestCase):
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
        """Test Twitter Enrollment context"""
        ak_context = TwitterOAuthCallback().get_user_enroll_context(TWITTER_USER)
        self.assertEqual(ak_context["username"], TWITTER_USER["data"]["username"])
        self.assertEqual(ak_context["email"], None)
        self.assertEqual(ak_context["name"], TWITTER_USER["data"]["name"])
