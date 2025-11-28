"""Test OAuth Source tasks"""

from django.test import TestCase
from requests_mock import Mocker

from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.tasks import update_well_known_jwks


class TestOAuthSourceTasks(TestCase):
    """Test OAuth Source tasks"""

    def setUp(self) -> None:
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key="",
        )

    @Mocker()
    def test_well_known_jwks(self, mock: Mocker):
        """Test well_known update"""
        self.source.oidc_well_known_url = "http://foo/.well-known/openid-configuration"
        self.source.save()
        mock.get(
            self.source.oidc_well_known_url,
            json={
                "authorization_endpoint": "foo",
                "token_endpoint": "foo",
                "userinfo_endpoint": "foo",
                "jwks_uri": "http://foo/jwks",
            },
        )
        mock.get("http://foo/jwks", json={"foo": "bar"})
        update_well_known_jwks.send()
        self.source.refresh_from_db()
        self.assertEqual(self.source.authorization_url, "foo")
        self.assertEqual(self.source.access_token_url, "foo")
        self.assertEqual(self.source.profile_url, "foo")
        self.assertEqual(self.source.oidc_jwks_url, "http://foo/jwks")
        self.assertEqual(
            self.source.oidc_jwks,
            {
                "foo": "bar",
            },
        )
