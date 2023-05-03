"""Patreon Type tests"""
from django.test import RequestFactory, TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.patreon import PatreonOAuthCallback

PATREON_USER = {
    "data": {
        "attributes": {
            "about": None,
            "created": "2017-10-20T21:36:23+00:00",
            "discord_id": None,
            "email": "corgi@example.com",
            "facebook": None,
            "facebook_id": None,
            "first_name": "Corgi",
            "full_name": "Corgi The Dev",
            "gender": 0,
            "has_password": True,
            "image_url": "https://c8.patreon.com/2/400/0000000",
            "is_deleted": False,
            "is_email_verified": False,
            "is_nuked": False,
            "is_suspended": False,
            "last_name": "The Dev",
            "social_connections": {
                "deviantart": None,
                "discord": None,
                "facebook": None,
                "reddit": None,
                "spotify": None,
                "twitch": None,
                "twitter": None,
                "youtube": None,
            },
            "thumb_url": "https://c8.patreon.com/2/100/0000000",
            "twitch": None,
            "twitter": None,
            "url": "https://www.patreon.com/corgithedev",
            "vanity": "corgithedev",
            "youtube": None,
        },
        "id": "0000000",
        "relationships": {"pledges": {"data": []}},
        "type": "user",
    },
    "links": {"self": "https://www.patreon.com/api/user/0000000"},
}


class TestTypePatreon(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="Patreon",
        )
        self.factory = RequestFactory()

    def test_enroll_context(self):
        """Test Patreon Enrollment context"""
        ak_context = PatreonOAuthCallback().get_user_enroll_context(PATREON_USER)
        self.assertEqual(ak_context["username"], PATREON_USER["data"]["attributes"]["vanity"])
        self.assertEqual(ak_context["email"], PATREON_USER["data"]["attributes"]["email"])
        self.assertEqual(ak_context["name"], PATREON_USER["data"]["attributes"]["full_name"])
