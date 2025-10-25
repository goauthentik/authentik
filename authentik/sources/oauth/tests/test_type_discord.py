"""Discord Type tests"""

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.discord import DiscordType

# https://discord.com/developers/docs/resources/user#user-object
DISCORD_USER = {
    "id": "80351110224678912",
    "username": "Nelly",
    "discriminator": "1337",
    "avatar": "8342729096ea3675442027381ff50dfe",
    "verified": True,
    "email": "nelly@discord.com",
    "flags": 64,
    "premium_type": 1,
    "public_flags": 64,
}


class TestTypeDiscord(TestCase):
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
        """Test discord Enrollment context"""
        ak_context = DiscordType().get_base_user_properties(source=self.source, info=DISCORD_USER)
        self.assertEqual(ak_context["username"], DISCORD_USER["username"])
        self.assertEqual(ak_context["email"], DISCORD_USER["email"])
        self.assertEqual(ak_context["name"], DISCORD_USER["username"])
