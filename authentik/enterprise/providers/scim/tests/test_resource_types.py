"""OAuth authentication failures in resource-type diagnostics."""

from datetime import timedelta

from django.core.cache import cache
from django.urls import reverse
from django.utils.timezone import now
from requests import ConnectionError
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.providers.scim.models import SCIMAuthenticationMode, SCIMProvider
from authentik.providers.scim.tests.test_resource_types import USER_TYPE, listing
from authentik.sources.oauth.models import OAuthSource, UserOAuthSourceConnection


class TestSCIMResourceTypesOAuth(APITestCase):
    """Exercise the real OAuth token initialization through the diagnostic API."""

    def setUp(self):
        cache.clear()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.token_url = "https://oauth.example.com/token"
        self.remote_url = "https://scim.example.com/v2/ResourceTypes"
        self.source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            access_token_url=self.token_url,
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            provider_type="openidconnect",
        )
        self.provider = SCIMProvider.objects.create(
            name=generate_id(),
            url="https://scim.example.com/v2",
            auth_mode=SCIMAuthenticationMode.OAUTH_INTERACTIVE,
            auth_oauth=self.source,
        )
        self.url = reverse("authentik_api:scimprovider-resource-types", args=[self.provider.pk])

    def create_expired_connection(self):
        return UserOAuthSourceConnection.objects.create(
            source=self.source,
            user=self.provider.auth_oauth_user,
            identifier=generate_id(),
            access_token=generate_id(),
            refresh_token=generate_id(),
            expires=now() - timedelta(seconds=1),
        )

    def assert_authentication_error(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "error")
        self.assertFalse(response.data["cached"])
        self.assertEqual(response.data["resource_types"], [])
        self.assertTrue(response.data["fetched_at"])
        self.assertIn("authentication", response.data["detail"])

    @Mocker()
    def test_missing_interactive_token(self, mock: Mocker):
        """An uninitialized interactive provider reports an authentication diagnostic."""
        self.assert_authentication_error(self.client.get(self.url))
        self.assertEqual(mock.call_count, 0)

    @Mocker()
    def test_rejected_refresh_token(self, mock: Mocker):
        """Token endpoint errors must not be classified as missing ResourceTypes support."""
        self.create_expired_connection()
        for status_code in (400, 401, 404, 501):
            with self.subTest(status_code=status_code):
                token_request = mock.post(
                    self.token_url,
                    status_code=status_code,
                    json={"error": "invalid_grant", "error_description": "private token details"},
                )
                response = self.client.get(self.url)
                self.assert_authentication_error(response)
                self.assertNotIn("private token details", response.data["detail"])
                self.assertEqual(token_request.call_count, 1)
        self.assertEqual(mock.call_count, 4)

    @Mocker()
    def test_unreachable_token_endpoint(self, mock: Mocker):
        self.create_expired_connection()
        mock.post(self.token_url, exc=ConnectionError)
        self.assert_authentication_error(self.client.get(self.url))
        self.assertEqual(mock.call_count, 1)

    @Mocker()
    def test_cached_discovery_does_not_refresh_oauth_token(self, mock: Mocker):
        """A cache hit needs no token; forced refresh retries auth and reports failures."""
        connection = self.create_expired_connection()
        mock.post(
            self.token_url,
            json={"access_token": "new-access-token", "expires_in": 3600},
        )
        mock.get(self.remote_url, json=listing([USER_TYPE]))
        first = self.client.get(self.url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["status"], "success")
        self.assertFalse(first.data["cached"])
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.last_request.headers["Authorization"], "Bearer new-access-token")

        UserOAuthSourceConnection.objects.filter(pk=connection.pk).update(
            expires=now() - timedelta(seconds=1)
        )
        mock.post(self.token_url, status_code=401, json={"error": "invalid_grant"})
        cached = self.client.get(self.url)
        self.assertEqual(cached.data["status"], "success")
        self.assertTrue(cached.data["cached"])
        self.assertEqual(cached.data["fetched_at"], first.data["fetched_at"])
        self.assertEqual(mock.call_count, 2)

        self.assert_authentication_error(self.client.get(self.url, {"refresh": "true"}))
        self.assertEqual(mock.call_count, 3)
        # A failed refresh clears the old success and is not itself cached.
        self.assert_authentication_error(self.client.get(self.url))
        self.assertEqual(mock.call_count, 4)
