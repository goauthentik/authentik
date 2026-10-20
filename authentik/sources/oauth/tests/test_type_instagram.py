"""Instagram Type tests"""

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.instagram import InstagramOAuthCallback, InstagramType

# https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login
INSTAGRAM_USER = {
    "user_id": "17841405793187218",
    "username": "foobar",
    "name": "Foo Bar",
    "account_type": "BUSINESS",
}


class TestTypeInstagram(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="instagram",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test Instagram Enrollment context"""
        ak_context = InstagramType().get_base_user_properties(
            source=self.source, info=INSTAGRAM_USER
        )
        self.assertEqual(ak_context["username"], INSTAGRAM_USER["username"])
        self.assertIsNone(ak_context["email"])
        self.assertEqual(ak_context["name"], INSTAGRAM_USER["name"])

    def test_user_id(self):
        """Test Instagram user ID, which is called user_id instead of id"""
        self.assertEqual(
            InstagramOAuthCallback().get_user_id(INSTAGRAM_USER), INSTAGRAM_USER["user_id"]
        )
        self.assertIsNone(InstagramOAuthCallback().get_user_id({}))
