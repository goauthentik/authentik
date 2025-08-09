"""Test Applications API with reserved slugs"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.providers.oauth2.models import OAuth2Provider, RedirectURI, RedirectURIMatchingMode


class TestApplicationsReservedSlugs(APITestCase):
    """Test applications API with reserved slugs"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)
        self.provider = OAuth2Provider.objects.create(
            name="test-oauth2",
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://some-domain")],
            authorization_flow=create_test_flow(),
        )

    def test_create_application_with_reserved_slug(self):
        """Test creating an application with a reserved slug"""
        response = self.client.post(
            reverse("authentik_api:application-list"),
            {
                "name": "Test Application",
                "slug": "authorize",
                "provider": self.provider.pk,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("reserved", response.data["slug"][0])

        response = self.client.post(
            reverse("authentik_api:application-list"),
            {
                "name": "Test Application",
                "slug": "token",
                "provider": self.provider.pk,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("reserved", response.data["slug"][0])

        response = self.client.post(
            reverse("authentik_api:application-list"),
            {
                "name": "Test Application",
                "slug": "userinfo",
                "provider": self.provider.pk,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("reserved", response.data["slug"][0])

        response = self.client.post(
            reverse("authentik_api:application-list"),
            {
                "name": "Test Application",
                "slug": "revoke",
                "provider": self.provider.pk,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("reserved", response.data["slug"][0])

    def test_update_application_with_reserved_slug(self):
        """Test updating an application to use a reserved slug"""
        app = Application.objects.create(
            name="Test Application",
            slug="valid-slug",
            provider=self.provider,
        )

        response = self.client.patch(
            reverse("authentik_api:application-detail", kwargs={"slug": app.slug}),
            {
                "slug": "authorize",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("reserved", response.data["slug"][0])

    def test_reserved_slugs_blocked_for_all_applications(self):
        """Test that reserved slugs are blocked for all applications regardless of provider"""
        reserved_slugs = ["authorize", "token", "device", "userinfo", "introspect", "revoke"]

        for slug in reserved_slugs:
            response = self.client.post(
                reverse("authentik_api:application-list"),
                {
                    "name": f"Test Application {slug}",
                    "slug": slug,
                },
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("slug", response.data)
            self.assertIn("reserved", response.data["slug"][0])

    def test_valid_slug_allowed(self):
        """Test that applications with valid slugs can be created with OAuth2 providers"""
        response = self.client.post(
            reverse("authentik_api:application-list"),
            {
                "name": "Valid App",
                "slug": "valid-app",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["slug"], "valid-app")

        response = self.client.patch(
            reverse("authentik_api:application-detail", kwargs={"slug": "valid-app"}),
            {
                "provider": self.provider.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["provider"], self.provider.pk)

        response = self.client.post(
            reverse("authentik_api:application-list"),
            {
                "name": "Another Valid App",
                "slug": "another-valid-app",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["slug"], "another-valid-app")

        from authentik.core.tests.utils import create_test_flow
        from authentik.providers.oauth2.models import (
            OAuth2Provider,
            RedirectURI,
            RedirectURIMatchingMode,
        )

        second_provider = OAuth2Provider.objects.create(
            name="test-oauth2-second",
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://some-other-domain")],
            authorization_flow=create_test_flow(),
        )

        response = self.client.patch(
            reverse("authentik_api:application-detail", kwargs={"slug": "another-valid-app"}),
            {
                "provider": second_provider.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["provider"], second_provider.pk)
