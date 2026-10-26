"""Test OAuth2 provider secret handling"""

from base64 import b64encode

from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.utils import provider_from_request
from authentik.providers.proxy.models import ProxyProvider


class TestProviderSecret(APITestCase):
    """Test OAuth2 provider secret handling"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_api_create_with_secret_reference(self):
        """The API accepts a reference to an existing secret"""
        secret = Secret.objects.create(name=generate_id())
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "client_secret_ref": str(secret.pk),
                "redirect_uris": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        provider = OAuth2Provider.objects.get(pk=response.json()["pk"])
        self.assertEqual(provider.client_secret_ref, secret)

    def test_api_create_with_empty_secret_reference(self):
        """An empty picker requests a generated secret."""
        for value in [None, ""]:
            with self.subTest(value=value):
                response = self.client.post(
                    reverse("authentik_api:oauth2provider-list"),
                    data={
                        "name": generate_id(),
                        "authorization_flow": create_test_flow().pk,
                        "invalidation_flow": create_test_flow().pk,
                        "client_secret_ref": value,
                        "redirect_uris": [],
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, 201, response.content)
                provider = OAuth2Provider.objects.get(pk=response.json()["pk"])
                self.assertTrue(provider.client_secret_ref.secret_value)

    def test_api_rejects_non_ascii_secret_reference(self):
        """OAuth client secrets must remain valid HTTP Basic credentials."""
        secret = Secret.objects.create(name=generate_id(), secret_value="non-ascii-ú")
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "client_secret_ref": str(secret.pk),
                "redirect_uris": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"client_secret_ref": ["Client secret must consist of only ASCII characters."]},
        )

    def test_api_rejects_incompatible_secret_reference(self):
        for secret_type, value in [
            (SecretType.JSON, "{}"),
            (SecretType.FILE, "aGk="),
            (SecretType.TEXT, "x" * 256),
        ]:
            with self.subTest(type=secret_type):
                secret = Secret.objects.create(
                    name=generate_id(), type=secret_type, secret_value=value
                )
                response = self.client.post(
                    reverse("authentik_api:oauth2provider-list"),
                    data={
                        "name": generate_id(),
                        "authorization_flow": create_test_flow().pk,
                        "invalidation_flow": create_test_flow().pk,
                        "client_secret_ref": str(secret.pk),
                        "redirect_uris": [],
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn("client_secret_ref", response.json())

    def test_replacement_preserves_oauth_constraints(self):
        provider = OAuth2Provider.objects.create(name=generate_id())
        secret = provider.client_secret_ref
        original = secret.secret_value
        for value in ["x" * 256, "non-ascii-ú", "line\nbreak"]:
            with self.subTest(value=value):
                response = self.client.patch(
                    reverse("authentik_api:secret-detail", kwargs={"pk": secret.pk}),
                    {"value": value},
                )
                self.assertEqual(response.status_code, 400, response.content)
                with self.assertRaises(ValidationError):
                    secret.validate_value(value)
                self.assertEqual(secret.secret_value, original)
                secret.refresh_from_db()
                self.assertEqual(secret.secret_value, original)
        secret.replace_value("x" * 255)
        secret.refresh_from_db()
        self.assertEqual(secret.secret_value, "x" * 255)

    def test_api_update_requires_secret_reference(self):
        """Clearing the reference of an existing provider must not replace its secret."""
        provider = OAuth2Provider.objects.create(name=generate_id())
        secret = provider.client_secret_ref
        response = self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider.pk}),
            data={"client_secret_ref": None},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        provider.refresh_from_db()
        self.assertEqual(provider.client_secret_ref, secret)

    def test_api_rejects_legacy_secret_field(self):
        """Sending the removed client_secret field fails instead of being ignored."""
        provider = OAuth2Provider.objects.create(name=generate_id())
        response = self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider.pk}),
            data={"client_secret": "legacy"},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("client_secret_ref", response.json()["client_secret"][0])

    def test_generated_secret_keeps_provider_length(self):
        """Generated client secrets don't depend on the default token length setting."""
        provider = OAuth2Provider.objects.create(name=generate_id())
        self.assertEqual(len(provider.client_secret_ref.secret_value), 128)

    def test_client_auth_loads_secret(self):
        """Authenticating a client reads its secret without another query."""
        provider = OAuth2Provider.objects.create(name=generate_id())
        credentials = b64encode(f"{provider.client_id}:secret".encode()).decode()
        request = RequestFactory().post("/", HTTP_AUTHORIZATION=f"Basic {credentials}")
        loaded, _, _ = provider_from_request(request)
        with self.assertNumQueries(0):
            self.assertEqual(
                loaded.client_secret_ref.secret_value, provider.client_secret_ref.secret_value
            )

    def test_generated_secret_access(self):
        """Roles that may change every provider can read secrets generated for new ones,
        without initial permissions, like they could before credentials moved to secrets."""
        user = create_test_user()
        user.assign_perms_to_managed_role(
            [
                "authentik_providers_oauth2.add_oauth2provider",
                "authentik_providers_oauth2.view_oauth2provider",
                "authentik_providers_oauth2.change_oauth2provider",
            ]
        )
        viewer = create_test_user()
        viewer.assign_perms_to_managed_role("authentik_providers_oauth2.view_oauth2provider")
        self.client.force_login(user)
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        secret = OAuth2Provider.objects.get(pk=response.json()["pk"]).client_secret_ref
        response = self.client.get(
            reverse("authentik_api:secret-view-value", kwargs={"pk": secret.pk})
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["value"], secret.secret_value)
        self.assertTrue(viewer.has_perm("authentik_crypto_secrets.view_secret", secret))
        self.assertFalse(viewer.has_perm("authentik_crypto_secrets.view_secret_value", secret))

        # Proxy providers are OAuth2 providers, so their client secrets follow the same
        # permissions, and their cookie secrets follow proxy provider permissions.
        proxy = ProxyProvider.objects.create(name=generate_id())
        self.assertTrue(
            user.has_perm("authentik_crypto_secrets.view_secret_value", proxy.client_secret_ref)
        )
        self.assertFalse(
            user.has_perm("authentik_crypto_secrets.view_secret", proxy.cookie_secret_ref)
        )
