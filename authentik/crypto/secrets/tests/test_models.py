"""Managed secret model tests."""

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase, TransactionTestCase

from authentik.crypto.secrets.models import Secret, SecretType, create_named_secret
from authentik.events.models import Event, EventAction


class TestSecret(TestCase):
    """Managed secret behavior."""

    def test_rotate(self):
        secret = Secret.objects.create(name="test")
        previous = secret.value

        value = secret.rotate()

        secret.refresh_from_db()
        self.assertEqual(secret.value, value)
        self.assertNotEqual(value, previous)
        self.assertEqual(len(value), 128)
        event = Event.objects.get(action=EventAction.SECRET_ROTATE)
        self.assertEqual(event.context["secret"]["pk"], secret.pk.hex)
        self.assertNotIn(value, str(event.context))

    def test_non_text_cannot_rotate(self):
        secret = Secret.objects.create(name="file", type=SecretType.FILE, value="aGk=")
        with self.assertRaises(ValueError):
            secret.rotate()

    def test_collision_safe_name(self):
        first = create_named_secret("consumer")
        second = create_named_secret("consumer")
        self.assertEqual(first.name, "consumer")
        self.assertEqual(second.name, "consumer (2)")

    def test_structured_values(self):
        for secret_type, value in [
            (SecretType.TEXT, '{"token": "value"}'),
            (SecretType.MULTILINE, "token: value\n"),
            (SecretType.FILE, "dG9rZW46IHZhbHVlCg=="),
        ]:
            with self.subTest(type=secret_type):
                self.assertEqual(
                    Secret(type=secret_type, value=value).get_json(), {"token": "value"}
                )

    def test_invalid_structured_values(self):
        for secret_type, value in [
            (SecretType.TEXT, "[]"),
            (SecretType.TEXT, "null"),
            (SecretType.TEXT, "{broken"),
            (SecretType.FILE, "not base64"),
            (SecretType.FILE, "/w=="),
        ]:
            with self.subTest(type=secret_type, value=value):
                with self.assertRaises(ValueError):
                    Secret(type=secret_type, value=value).get_json()

    def test_replacing_unchanged_value_does_not_audit_rotation(self):
        secret = Secret.objects.create(name="unchanged", value="current")
        secret.replace_value("current")
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())

    def test_invalid_file_replacement_preserves_value(self):
        secret = Secret.objects.create(name="file", type=SecretType.FILE, value="aGk=")
        with self.assertRaises(ValidationError):
            secret.replace_value("not base64")
        self.assertEqual(secret.value, "aGk=")
        secret.refresh_from_db()
        self.assertEqual(secret.value, "aGk=")
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())

    def test_failed_rotation_restores_value_and_timestamp(self):
        secret = Secret.objects.create(name="rollback", value="old")
        previous_updated = secret.last_updated
        with (
            patch(
                "authentik.crypto.secrets.models.secret_value_changed.send",
                side_effect=RuntimeError("consumer failed"),
            ),
            self.assertRaises(RuntimeError),
        ):
            secret.rotate()
        self.assertEqual(secret.value, "old")
        self.assertEqual(secret.last_updated, previous_updated)
        secret.refresh_from_db()
        self.assertEqual(secret.value, "old")
        self.assertEqual(secret.last_updated, previous_updated)
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())


class TestCommittedSecret(TransactionTestCase):
    def test_callback_failure_keeps_committed_value(self):
        secret = Secret.objects.create(name="committed", value="old")

        def schedule_failure(**kwargs):
            def fail():
                raise RuntimeError("outpost unavailable")

            transaction.on_commit(fail)

        with (
            patch(
                "authentik.crypto.secrets.models.secret_value_changed.send",
                side_effect=schedule_failure,
            ),
            self.assertRaises(RuntimeError),
        ):
            secret.replace_value("new")
        self.assertEqual(secret.value, "new")
        secret.refresh_from_db()
        self.assertEqual(secret.value, "new")
        self.assertTrue(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())
