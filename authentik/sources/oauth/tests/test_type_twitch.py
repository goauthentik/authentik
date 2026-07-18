"""Twitch Type tests"""

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.twitch import TwitchType

# https://dev.twitch.tv/docs/authentication/getting-tokens-oidc/#getting-claims-information-from-an-access-token
TWITCH_USER = {
    "aud": "ym2tq9o71tikh2zyebksiture1hzg5",
    "exp": 1665261184,
    "iat": 1665260184,
    "iss": "https://id.twitch.tv/oauth2",
    "sub": "603916897",
    "email": "foo@bar.baz",
    "preferred_username": "FooBar",
}


class TestTypeTwitch(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="twitch",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test twitch Enrollment context"""
        ak_context = TwitchType().get_base_user_properties(source=self.source, info=TWITCH_USER)
        self.assertEqual(ak_context["username"], TWITCH_USER["preferred_username"])
        self.assertEqual(ak_context["email"], TWITCH_USER["email"])
        self.assertEqual(ak_context["name"], TWITCH_USER["preferred_username"])
