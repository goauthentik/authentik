"""GETTING REMOVED WHEN FRONTEND IS DONE: verify old form credentials."""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.crypto.secrets.models import Secret
from authentik.events.models import Event, EventAction
from authentik.providers.oauth2.models import OAuth2Provider


class TestLegacySecretAPI(APITestCase):
    def setUp(self):
        self.client.force_login(create_test_admin_user())
        self.provider = OAuth2Provider.objects.create(name="legacy")
        self.url = reverse("authentik_api:oauth2provider-detail", kwargs={"pk": self.provider.pk})

    def test_create_from_old_form(self):
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            {
                "name": "old form",
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {"matching_mode": "strict", "url": "https://example.com/callback"}
                ],
                "client_secret": "  supplied credential  ",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        provider = OAuth2Provider.objects.get(pk=response.json()["pk"])
        self.assertEqual(provider.secret.value, "  supplied credential  ")

    def test_edit_does_not_rotate_shared_secret(self):
        original = self.provider.secret
        other = OAuth2Provider.objects.create(name="other", secret=original)
        response = self.client.patch(self.url, {"client_secret": "replacement"})
        self.assertEqual(response.status_code, 200, response.content)
        self.provider.refresh_from_db()
        other.refresh_from_db()
        self.assertNotEqual(self.provider.secret_id, other.secret_id)
        self.assertEqual(self.provider.secret.value, "replacement")
        self.assertEqual(other.secret.value, original.value)

    def test_unchanged_value_preserves_reference(self):
        original = self.provider.secret
        count = Secret.objects.count()
        response = self.client.patch(self.url, {"client_secret": original.value})
        self.assertEqual(response.status_code, 200, response.content)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.secret_id, original.pk)
        self.assertEqual(Secret.objects.count(), count)

    def test_invalid_input_does_not_create_secrets(self):
        count = Secret.objects.count()
        for payload in [
            {"client_secret": "non-ascii-ú"},
            {"client_secret": "valid", "client_id": "non-ascii-ú"},
            {"client_secret": "valid", "secret": str(self.provider.secret_id)},
        ]:
            with self.subTest(payload=payload):
                response = self.client.patch(self.url, payload)
                self.assertEqual(response.status_code, 400, response.content)
                self.assertEqual(Secret.objects.count(), count)

    def test_legacy_reads_require_value_permission(self):
        user = create_test_user()
        user.assign_perms_to_managed_role(
            "authentik_providers_oauth2.view_oauth2provider", self.provider
        )
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("client_secret", response.json())
        user.assign_perms_to_managed_role(
            "authentik_secrets.view_secret_value", self.provider.secret
        )
        self.assertEqual(
            self.client.get(self.url).json()["client_secret"], self.provider.secret.value
        )
        self.assertTrue(Event.objects.filter(action=EventAction.SECRET_VIEW).exists())
