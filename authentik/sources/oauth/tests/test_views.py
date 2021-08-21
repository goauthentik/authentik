"""OAuth Source tests"""
from django.test import TestCase
from django.urls import reverse

from authentik.sources.oauth.api.source import OAuthSourceSerializer
from authentik.sources.oauth.models import OAuthSource


class TestOAuthSource(TestCase):
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

    def test_api_validate(self):
        """Test API validation"""
        self.assertTrue(
            OAuthSourceSerializer(
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "google",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                }
            ).is_valid()
        )
        self.assertFalse(
            OAuthSourceSerializer(
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "openidconnect",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                }
            ).is_valid()
        )

    def test_source_redirect(self):
        """test redirect view"""
        self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-login",
                kwargs={"source_slug": self.source.slug},
            )
        )

    def test_source_callback(self):
        """test callback view"""
        self.client.get(
            reverse(
                "authentik_sources_oauth:oauth-client-callback",
                kwargs={"source_slug": self.source.slug},
            )
        )
