"""bsky model tests"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now

from authentik.sources.bsky.models import BskySource, UserBskySourceConnection


class TestBskySource(TestCase):
    """bsky Source tests"""

    def setUp(self):
        self.source: BskySource = BskySource.objects.create(
            name="test",
            slug="test",
        )

    def test_login_challenge(self):
        """Test ui_login_button returns a valid challenge"""
        ui_login_button = self.source.ui_login_button(None)
        self.assertTrue(ui_login_button.challenge.is_valid(raise_exception=True))

    def test_user_base_properties(self):
        """Test get_base_user_properties maps handle/displayName from a sample profile dict"""
        profile = {"did": "did:plc:test", "handle": "user.bsky.social", "displayName": "User"}
        properties = self.source.get_base_user_properties(info=profile)
        self.assertEqual(
            properties,
            {
                "username": "user.bsky.social",
                "name": "User",
            },
        )

    def test_user_base_properties_no_display_name(self):
        """Test get_base_user_properties falls back to handle when displayName is absent"""
        profile = {"did": "did:plc:test", "handle": "user.bsky.social"}
        properties = self.source.get_base_user_properties(info=profile)
        self.assertEqual(properties["name"], "user.bsky.social")

    def test_ui_user_settings_configure_url(self):
        """Test ui_user_settings() sets configure_url to the oauth-client-login URL.

        object_uid isn't set by ui_user_settings() itself - the real caller
        (SourceViewSet.user_settings) injects it via initial_data before
        validating, so this test does the same rather than calling is_valid()
        on the bare serializer."""
        settings = self.source.ui_user_settings()
        settings.initial_data["object_uid"] = self.source.slug
        self.assertTrue(settings.is_valid(raise_exception=True))
        expected_url = reverse(
            "authentik_sources_bsky:oauth-client-login",
            kwargs={"source_slug": self.source.slug},
        )
        self.assertEqual(settings.validated_data["configure_url"], expected_url)


class TestUserBskySourceConnection(TestCase):
    """UserBskySourceConnection tests"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_is_valid_before_expiry(self):
        """Test is_valid is True when expires is in the future"""
        connection = UserBskySourceConnection(
            source=self.source,
            access_token="token",
            expires=now() + timedelta(hours=1),
        )
        self.assertTrue(connection.is_valid)

    def test_is_valid_after_expiry(self):
        """Test is_valid is False when expires is in the past"""
        connection = UserBskySourceConnection(
            source=self.source,
            access_token="token",
            expires=now() - timedelta(hours=1),
        )
        self.assertFalse(connection.is_valid)
