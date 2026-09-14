"""Managed secret API tests."""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.events.models import Event, EventAction


class TestSecretsAPI(APITestCase):
    """Secret values require permissions separate from metadata."""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user = create_test_user()
        self.secret = Secret.objects.create(name="test")

    def test_create_generated(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("authentik_api:secret-list"), {"name": "created"})
        self.assertEqual(response.status_code, 201, response.content)
        secret = Secret.objects.get(name="created")
        self.assertTrue(secret.value)
        self.assertNotIn(secret.value, response.content.decode())

    def test_value_whitespace_is_preserved(self):
        self.client.force_login(self.admin)
        for secret_type in [SecretType.TEXT, SecretType.MULTILINE]:
            with self.subTest(type=secret_type):
                value = "  exact credential\n"
                response = self.client.post(
                    reverse("authentik_api:secret-list"),
                    {"name": secret_type, "type": secret_type, "value": value},
                )
                self.assertEqual(response.status_code, 201, response.content)
                secret = Secret.objects.get(pk=response.json()["pk"])
                self.assertEqual(secret.value, value)

                response = self.client.patch(
                    reverse("authentik_api:secret-detail", kwargs={"pk": secret.pk}),
                    {"value": " replacement "},
                )
                self.assertEqual(response.status_code, 200, response.content)
                secret.refresh_from_db()
                self.assertEqual(secret.value, " replacement ")

    def test_view_value_permission_and_audit(self):
        self.user.assign_perms_to_managed_role("authentik_secrets.view_secret", self.secret)
        self.client.force_login(self.user)
        url = reverse("authentik_api:secret-view-value", kwargs={"pk": self.secret.pk})
        self.assertEqual(self.client.get(url).status_code, 403)

        self.user.assign_perms_to_managed_role("authentik_secrets.view_secret_value", self.secret)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"value": self.secret.value})
        self.assertTrue(Event.objects.filter(action=EventAction.SECRET_VIEW).exists())

    def test_rotate_permission_and_disclosure(self):
        self.user.assign_perms_to_managed_role("authentik_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role("authentik_secrets.rotate_secret", self.secret)
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:secret-rotate", kwargs={"pk": self.secret.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["value"])

    def test_rotation_requires_permission_and_returns_value_only_when_allowed(self):
        self.user.assign_perms_to_managed_role("authentik_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role("authentik_secrets.view_secret_value", self.secret)
        self.client.force_login(self.user)
        url = reverse("authentik_api:secret-rotate", kwargs={"pk": self.secret.pk})
        previous = self.secret.value
        self.assertEqual(self.client.post(url).status_code, 403)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.value, previous)

        self.user.assign_perms_to_managed_role("authentik_secrets.rotate_secret", self.secret)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.secret.refresh_from_db()
        self.assertEqual(response.json()["value"], self.secret.value)
        self.assertNotEqual(self.secret.value, previous)

    def test_type_cannot_change_after_creation(self):
        self.client.force_login(self.admin)
        response = self.client.patch(
            reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}),
            {"type": SecretType.FILE, "value": "aGk="},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("type", response.json())
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.type, SecretType.TEXT)

    def test_replace_value_requires_rotate_permission(self):
        self.user.assign_perms_to_managed_role("authentik_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role("authentik_secrets.change_secret", self.secret)
        self.client.force_login(self.user)
        url = reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk})
        response = self.client.patch(url, {"value": "replacement"})
        self.assertEqual(response.status_code, 403)
        self.secret.refresh_from_db()
        self.assertNotEqual(self.secret.value, "replacement")

        self.user.assign_perms_to_managed_role("authentik_secrets.rotate_secret", self.secret)
        response = self.client.patch(url, {"value": "replacement"})
        self.assertEqual(response.status_code, 200, response.content)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.value, "replacement")

    def test_file_validation_and_rotation(self):
        self.client.force_login(self.admin)
        list_url = reverse("authentik_api:secret-list")
        response = self.client.post(list_url, {"name": "file", "type": "file"})
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            list_url, {"name": "file", "type": "file", "value": "not base64"}
        )
        self.assertEqual(response.status_code, 400)
        secret = Secret.objects.create(name="file", type=SecretType.FILE, value="aGk=")
        response = self.client.post(
            reverse("authentik_api:secret-rotate", kwargs={"pk": secret.pk})
        )
        self.assertEqual(response.status_code, 400)

    def test_blank_value_keeps_existing_value_without_rotate_permission(self):
        self.user.assign_perms_to_managed_role("authentik_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role("authentik_secrets.change_secret", self.secret)
        self.client.force_login(self.user)
        previous = self.secret.value

        response = self.client.patch(
            reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}),
            {"name": "renamed", "value": ""},
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.name, "renamed")
        self.assertEqual(self.secret.value, previous)
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())
