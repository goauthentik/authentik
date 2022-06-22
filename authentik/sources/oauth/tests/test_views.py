"""OAuth Source tests"""
from django.test import TestCase
from django.urls import reverse
from requests_mock import Mocker

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
                    "oidc_well_known_url": "",
                    "oidc_jwks_url": "",
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

    def test_api_validate_openid_connect(self):
        """Test API validation (with OIDC endpoints)"""
        openid_config = {
            "authorization_endpoint": "http://mock/oauth/authorize",
            "token_endpoint": "http://mock/oauth/token",
            "userinfo_endpoint": "http://mock/oauth/userinfo",
            "jwks_uri": "http://mock/oauth/discovery/keys",
        }
        jwks_config = {"keys": []}
        with Mocker() as mocker:
            url = "http://mock/.well-known/openid-configuration"
            mocker.get(url, json=openid_config)
            mocker.get(openid_config["jwks_uri"], json=jwks_config)
            serializer = OAuthSourceSerializer(
                instance=self.source,
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "openidconnect",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                    "authorization_url": "http://foo",
                    "access_token_url": "http://foo",
                    "profile_url": "http://foo",
                    "oidc_well_known_url": url,
                    "oidc_jwks_url": "",
                },
            )
            self.assertTrue(serializer.is_valid())
            self.assertEqual(
                serializer.validated_data["authorization_url"], "http://mock/oauth/authorize"
            )
            self.assertEqual(
                serializer.validated_data["access_token_url"], "http://mock/oauth/token"
            )
            self.assertEqual(serializer.validated_data["profile_url"], "http://mock/oauth/userinfo")
            self.assertEqual(
                serializer.validated_data["oidc_jwks_url"], "http://mock/oauth/discovery/keys"
            )
            self.assertEqual(serializer.validated_data["oidc_jwks"], jwks_config)

    def test_api_validate_openid_connect_invalid(self):
        """Test API validation (with OIDC endpoints)"""
        openid_config = {}
        with Mocker() as mocker:
            url = "http://mock/.well-known/openid-configuration"
            mocker.get(url, json=openid_config)
            serializer = OAuthSourceSerializer(
                instance=self.source,
                data={
                    "name": "foo",
                    "slug": "bar",
                    "provider_type": "openidconnect",
                    "consumer_key": "foo",
                    "consumer_secret": "foo",
                    "authorization_url": "http://foo",
                    "access_token_url": "http://foo",
                    "profile_url": "http://foo",
                    "oidc_well_known_url": url,
                    "oidc_jwks_url": "",
                },
            )
            self.assertFalse(serializer.is_valid())

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
