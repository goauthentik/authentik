"""Twitter Type tests"""

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.twitter import TwitterType

# https://developer.twitter.com/en/docs/twitter-api/users/lookup/api-reference/get-users-me
TWITTER_USER = {"data": {"id": "2244994945", "name": "TwitterDev", "username": "Twitter Dev"}}
TWITTER_USER_WITH_EMAIL = {
    "data": {
        "id": "2244994945",
        "name": "TwitterDev",
        "username": "Twitter Dev",
        "confirmed_email": "test@example.com",
    }
}


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
        ak_context = TwitterType().get_base_user_properties(source=self.source, info=TWITTER_USER)
        self.assertEqual(ak_context["username"], TWITTER_USER["data"]["username"])
        self.assertEqual(ak_context["email"], None)
        self.assertEqual(ak_context["name"], TWITTER_USER["data"]["name"])

    def test_enroll_context_with_email(self):
        """Test Twitter Enrollment context with email"""
        ak_context = TwitterType().get_base_user_properties(
            source=self.source, info=TWITTER_USER_WITH_EMAIL
        )
        self.assertEqual(ak_context["username"], TWITTER_USER_WITH_EMAIL["data"]["username"])
        self.assertEqual(ak_context["email"], TWITTER_USER_WITH_EMAIL["data"]["confirmed_email"])
        self.assertEqual(ak_context["name"], TWITTER_USER_WITH_EMAIL["data"]["name"])
