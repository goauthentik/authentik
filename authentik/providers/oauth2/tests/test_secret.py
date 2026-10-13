"""Test OAuth2 provider secret handling"""

from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider


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
                    secret.replace_value(value)
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
