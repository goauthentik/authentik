"""Test OAuth2 End Session (RP-Initiated Logout) implementation"""

from django.test import RequestFactory
from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_brand, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RedirectURIType,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.end_session import EndSessionView


class TestEndSessionView(OAuthTestCase):
    """Test EndSessionView validation"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.invalidation_flow = create_test_flow()
        self.app = Application.objects.create(name=generate_id(), slug="test-app")
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            invalidation_flow=self.invalidation_flow,
            redirect_uris=[
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    "http://testserver/callback",
                    RedirectURIType.AUTHORIZATION,
                ),
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    "http://testserver/logout",
                    RedirectURIType.LOGOUT,
                ),
                RedirectURI(
                    RedirectURIMatchingMode.REGEX,
                    r"https://.*\.example\.com/logout",
                    RedirectURIType.LOGOUT,
                ),
            ],
        )
        self.app.provider = self.provider
        self.app.save()
        # Ensure brand has an invalidation flow
        self.brand = create_test_brand()
        self.brand.flow_invalidation = self.invalidation_flow
        self.brand.save()

    def test_post_logout_redirect_uri_strict_match(self):
        """Test strict URI matching redirects to flow"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {"post_logout_redirect_uri": "http://testserver/logout"},
            HTTP_HOST=self.brand.domain,
        )
        # Should redirect to the invalidation flow
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.invalidation_flow.slug, response.url)

    def test_post_logout_redirect_uri_strict_no_match(self):
        """Test strict URI not matching still proceeds with flow (no redirect URI in context)"""
        self.client.force_login(self.user)
        invalid_uri = "http://testserver/other"
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {"post_logout_redirect_uri": invalid_uri},
            HTTP_HOST=self.brand.domain,
        )
        # Should still redirect to flow, but invalid URI should not be in response
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(invalid_uri, response.url)

    def test_post_logout_redirect_uri_regex_match(self):
        """Test regex URI matching redirects to flow"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {"post_logout_redirect_uri": "https://app.example.com/logout"},
            HTTP_HOST=self.brand.domain,
        )
        # Should redirect to the invalidation flow
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.invalidation_flow.slug, response.url)

    def test_post_logout_redirect_uri_regex_no_match(self):
        """Test regex URI not matching"""
        self.client.force_login(self.user)
        invalid_uri = "https://malicious.com/logout"
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {"post_logout_redirect_uri": invalid_uri},
            HTTP_HOST=self.brand.domain,
        )
        # Should still proceed to flow, but invalid URI should not be in response
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(invalid_uri, response.url)

    def test_state_parameter_appended_to_uri(self):
        """Test state parameter is appended to validated redirect URI"""
        factory = RequestFactory()
        request = factory.get(
            "/end-session/",
            {
                "post_logout_redirect_uri": "http://testserver/logout",
                "state": "test-state-123",
            },
        )
        request.user = self.user
        request.brand = self.brand

        view = EndSessionView()
        view.request = request
        view.kwargs = {"application_slug": self.app.slug}
        view.resolve_provider_application()

        self.assertIn("state=test-state-123", view.post_logout_redirect_uri)

    def test_post_method(self):
        """Test POST requests work same as GET"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "authentik_providers_oauth2:end-session",
                kwargs={"application_slug": self.app.slug},
            ),
            {
                "post_logout_redirect_uri": "http://testserver/logout",
                "state": "xyz789",
            },
            HTTP_HOST=self.brand.domain,
        )
        self.assertEqual(response.status_code, 302)


class TestEndSessionAPI(OAuthTestCase):
    """Test End Session API functionality"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_post_logout_redirect_uris_create(self):
        """Test creating provider with post_logout redirect_uris"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/callback",
                        "redirect_uri_type": "authorization",
                    },
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/logout",
                        "redirect_uri_type": "logout",
                    },
                    {
                        "matching_mode": "regex",
                        "url": "https://.*\\.example\\.com/logout",
                        "redirect_uri_type": "logout",
                    },
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        provider_data = response.json()
        post_logout_uris = [
            u for u in provider_data["redirect_uris"] if u["redirect_uri_type"] == "logout"
        ]
        self.assertEqual(len(post_logout_uris), 2)

    def test_post_logout_redirect_uris_invalid_regex(self):
        """Test that invalid regex patterns are rejected"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/callback",
                        "redirect_uri_type": "authorization",
                    },
                    {
                        "matching_mode": "regex",
                        "url": "**invalid**",
                        "redirect_uri_type": "logout",
                    },
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("redirect_uris", response.json())

    def test_post_logout_redirect_uris_update(self):
        """Test updating redirect_uris with logout type"""
        # First create a provider
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    "http://testserver/callback",
                    RedirectURIType.AUTHORIZATION,
                ),
            ],
        )

        # Update with post_logout redirect URIs
        response = self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider.pk}),
            data={
                "redirect_uris": [
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/callback",
                        "redirect_uri_type": "authorization",
                    },
                    {
                        "matching_mode": "strict",
                        "url": "http://testserver/logout",
                        "redirect_uri_type": "logout",
                    },
                ],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify the update
        provider.refresh_from_db()
        self.assertEqual(len(provider.post_logout_redirect_uris), 1)
        self.assertEqual(provider.post_logout_redirect_uris[0].url, "http://testserver/logout")
