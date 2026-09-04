"""Test OAuth2 provider secret handling"""

from base64 import b64encode

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import ClientType, OAuth2Provider
from authentik.secrets.models import Secret


class TestProviderSecret(APITestCase):
    """Test OAuth2 provider secret handling"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_auto_create(self):
        """Creating a provider without a secret creates one with a generated value"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        self.assertIsNotNone(provider.secret)
        self.assertNotEqual(provider.secret.get_value(), "")
        self.assertEqual(provider.secret.value, provider.secret.get_value())

    def test_rotation_applies(self):
        """Rotating the secret changes what the provider authenticates with"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        old_value = provider.secret.get_value()
        provider.secret.rotate()
        provider.refresh_from_db()
        self.assertNotEqual(provider.secret.get_value(), old_value)

    def test_detached_secret_fails_closed(self):
        """A confidential provider whose secret is detached must reject empty-secret auth"""
        from django.test import RequestFactory

        from authentik.providers.oauth2.utils import authenticate_provider

        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_type=ClientType.CONFIDENTIAL,
            authorization_flow=create_test_flow(),
        )
        OAuth2Provider.objects.filter(pk=provider.pk).update(secret=None)
        provider.refresh_from_db()
        self.assertIsNone(provider.secret)
        auth = b64encode(f"{provider.client_id}:".encode()).decode()
        request = RequestFactory().get("/", HTTP_AUTHORIZATION=f"Basic {auth}")
        self.assertIsNone(authenticate_provider(request))

    def test_api_create_with_secret_reference(self):
        """The API accepts a reference to an existing secret"""
        secret = Secret.objects.create(name=generate_id())
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "secret": str(secret.pk),
                "redirect_uris": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        provider = OAuth2Provider.objects.get(pk=response.json()["pk"])
        self.assertEqual(provider.secret, secret)

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
                        "secret": value,
                        "redirect_uris": [],
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, 201, response.content)
                provider = OAuth2Provider.objects.get(pk=response.json()["pk"])
                self.assertTrue(provider.secret.value)

    def test_api_rejects_non_ascii_secret_reference(self):
        """OAuth client secrets must remain valid HTTP Basic credentials."""
        secret = Secret.objects.create(name=generate_id(), value="non-ascii-ú")
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "secret": str(secret.pk),
                "redirect_uris": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"secret": ["Client secret must consist of only ASCII characters."]},
        )
