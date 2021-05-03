"""google Type tests"""
from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.google import GoogleOAuth2Callback

# https://developers.google.com/identity/protocols/oauth2/openid-connect?hl=en
GOOGLE_USER = {
    "id": "1324813249123401234",
    "email": "foo@bar.baz",
    "verified_email": True,
    "name": "foo bar",
    "given_name": "foo",
    "family_name": "bar",
    "picture": "",
    "locale": "en",
}


class TestTypeGoogle(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="google",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test Google Enrollment context"""
        ak_context = GoogleOAuth2Callback().get_user_enroll_context(GOOGLE_USER)
        self.assertEqual(ak_context["username"], GOOGLE_USER["email"])
        self.assertEqual(ak_context["email"], GOOGLE_USER["email"])
        self.assertEqual(ak_context["name"], GOOGLE_USER["name"])
