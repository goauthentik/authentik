"""OAuth Source tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase

from authentik.sources.oauth.models import OAuthSource


class OAuthSourceTests(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.client = Client()
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openid-connect",
            authorization_url="",
            profile_url="",
            consumer_key="",
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
