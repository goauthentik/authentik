"""Mailcow Type tests"""

from django.test import TestCase

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.mailcow import MailcowType

# https://community.mailcow.email/d/13-mailcow-oauth-json-format/2
MAILCOW_USER = {
    "success": True,
    "username": "email@example.com",
    "identifier": "email@example.com",
    "email": "email@example.com",
    "full_name": "Example User",
    "displayName": "Example User",
    "created": "2020-05-15 11:33:08",
    "modified": "2020-05-15 12:23:31",
    "active": 1,
}


class TestTypeMailcow(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="mailcow",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    def test_enroll_context(self):
        """Test mailcow Enrollment context"""
        ak_context = MailcowType().get_base_user_properties(source=self.source, info=MAILCOW_USER)
        self.assertEqual(ak_context["email"], MAILCOW_USER["email"])
        self.assertEqual(ak_context["name"], MAILCOW_USER["full_name"])
