"""Managed secret API tests."""

from unittest.mock import PropertyMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.crypto.secrets.api import SecretSerializer
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
        self.assertTrue(secret.secret_value)
        self.assertNotIn(secret.secret_value, response.content.decode())

    def test_create_generated_with_length(self):
        self.client.force_login(self.admin)
        list_url = reverse("authentik_api:secret-list")
        response = self.client.post(list_url, {"name": "long", "length": 128})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(len(Secret.objects.get(name="long").secret_value), 128)
        for data in [
            {"name": "given", "length": 128, "value": "given"},
            {"name": "json", "length": 128, "type": "json", "value": "{}"},
        ]:
            with self.subTest(data=data):
                response = self.client.post(list_url, data)
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn("length", response.json())

    def test_value_whitespace_is_preserved(self):
        self.client.force_login(self.admin)
        value = "  -----BEGIN KEY-----\nexact credential\n"
        response = self.client.post(
            reverse("authentik_api:secret-list"), {"name": "whitespace", "value": value}
        )
        self.assertEqual(response.status_code, 201, response.content)
        secret = Secret.objects.get(pk=response.json()["pk"])
        self.assertEqual(secret.secret_value, value)

        response = self.client.patch(
            reverse("authentik_api:secret-detail", kwargs={"pk": secret.pk}),
            {"value": " replacement "},
        )
        self.assertEqual(response.status_code, 200, response.content)
        secret.refresh_from_db()
        self.assertEqual(secret.secret_value, " replacement ")

    def test_view_value_permission_and_audit(self):
        self.user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret", self.secret)
        self.client.force_login(self.user)
        url = reverse("authentik_api:secret-view-value", kwargs={"pk": self.secret.pk})
        self.assertEqual(self.client.get(url).status_code, 403)

        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.view_secret_value", self.secret
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"value": self.secret.secret_value})
        self.assertTrue(Event.objects.filter(action=EventAction.SECRET_VIEW).exists())

    def test_rotate_permission_and_disclosure(self):
        self.user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.rotate_secret", self.secret
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("authentik_api:secret-rotate", kwargs={"pk": self.secret.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["value"])

    def test_rotation_requires_permission_and_returns_value_only_when_allowed(self):
        self.user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.view_secret_value", self.secret
        )
        self.client.force_login(self.user)
        url = reverse("authentik_api:secret-rotate", kwargs={"pk": self.secret.pk})
        previous = self.secret.secret_value
        self.assertEqual(self.client.post(url).status_code, 403)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.secret_value, previous)

        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.rotate_secret", self.secret
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.secret.refresh_from_db()
        self.assertEqual(response.json()["value"], self.secret.secret_value)
        self.assertNotEqual(self.secret.secret_value, previous)

    def test_global_permissions_allow_replacement_and_rotation_disclosure(self):
        self.user.assign_perms_to_managed_role(
            [
                "authentik_crypto_secrets.view_secret",
                "authentik_crypto_secrets.change_secret",
                "authentik_crypto_secrets.rotate_secret",
                "authentik_crypto_secrets.view_secret_value",
            ]
        )
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}),
            {"value": "replacement"},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.secret_value, "replacement")
        response = self.client.post(
            reverse("authentik_api:secret-rotate", kwargs={"pk": self.secret.pk})
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.secret.refresh_from_db()
        self.assertEqual(response.json()["value"], self.secret.secret_value)

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
        self.user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.change_secret", self.secret
        )
        self.client.force_login(self.user)
        url = reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk})
        response = self.client.patch(url, {"value": "replacement"})
        self.assertEqual(response.status_code, 403)
        self.secret.refresh_from_db()
        self.assertNotEqual(self.secret.secret_value, "replacement")

        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.rotate_secret", self.secret
        )
        response = self.client.patch(url, {"value": "replacement"})
        self.assertEqual(response.status_code, 200, response.content)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.secret_value, "replacement")

    def test_file_validation_and_rotation(self):
        self.client.force_login(self.admin)
        list_url = reverse("authentik_api:secret-list")
        response = self.client.post(list_url, {"name": "file", "type": "file"})
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            list_url, {"name": "file", "type": "file", "value": "not base64"}
        )
        self.assertEqual(response.status_code, 400)
        secret = Secret.objects.create(name="file", type=SecretType.FILE, secret_value="aGk=")
        response = self.client.patch(
            reverse("authentik_api:secret-detail", kwargs={"pk": secret.pk}),
            {"value": "not base64"},
        )
        self.assertEqual(response.status_code, 400)
        secret.refresh_from_db()
        self.assertEqual(secret.secret_value, "aGk=")
        response = self.client.post(
            reverse("authentik_api:secret-rotate", kwargs={"pk": secret.pk})
        )
        self.assertEqual(response.status_code, 400)

    def test_json_validation(self):
        self.client.force_login(self.admin)
        list_url = reverse("authentik_api:secret-list")
        for value in ["[]", "plain", "{broken", "date: 2026-01-01"]:
            with self.subTest(value=value):
                response = self.client.post(
                    list_url, {"name": "json", "type": "json", "value": value}
                )
                self.assertEqual(response.status_code, 400, response.content)
                self.assertNotIn(value, response.content.decode())
        response = self.client.post(
            list_url, {"name": "json", "type": "json", "value": "token: value\n"}
        )
        self.assertEqual(response.status_code, 201, response.content)
        secret = Secret.objects.get(name="json")
        self.assertEqual(secret.get_json(), {"token": "value"})
        response = self.client.post(
            reverse("authentik_api:secret-rotate", kwargs={"pk": secret.pk})
        )
        self.assertEqual(response.status_code, 400)

    def test_filter_compatible_types(self):
        self.client.force_login(self.admin)
        Secret.objects.create(name="json", type=SecretType.JSON, secret_value="{}")
        Secret.objects.create(name="file", type=SecretType.FILE, secret_value="aGk=")
        response = self.client.get(reverse("authentik_api:secret-list"), {"type__in": "json,file"})
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            [secret["type"] for secret in response.json()["results"]], ["json", "file"]
        )

    def test_blank_value_keeps_existing_value_without_rotate_permission(self):
        self.user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret", self.secret)
        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.change_secret", self.secret
        )
        self.client.force_login(self.user)
        previous = self.secret.secret_value

        response = self.client.patch(
            reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}),
            {"name": "renamed", "value": ""},
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.name, "renamed")
        self.assertEqual(self.secret.secret_value, previous)
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())

    def test_failed_replacement_rolls_back_metadata(self):
        serializer = SecretSerializer(
            instance=self.secret, data={"name": "renamed", "value": "replacement"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with (
            patch(
                "authentik.crypto.secrets.models.secret_value_changed.send",
                side_effect=RuntimeError("consumer failed"),
            ),
            self.assertRaises(RuntimeError),
        ):
            serializer.save()
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.name, "test")
        self.assertNotEqual(self.secret.secret_value, "replacement")
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())

    @patch(
        "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware.enabled",
        PropertyMock(return_value=True),
    )
    def test_audit_diff_hides_value(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("authentik_api:secret-list"), {"name": "audited", "value": "audited-value"}
        )
        self.assertEqual(response.status_code, 201, response.content)
        event = Event.objects.get(action=EventAction.MODEL_CREATED, context__model__name="audited")
        self.assertIn("secret_value", event.context["diff"])
        self.assertNotIn("audited-value", str(event.context))
