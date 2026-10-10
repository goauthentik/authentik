"""Managed secret model tests."""

from traceback import format_exception
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from authentik.admin.models import DEFAULT_TOKEN_LENGTH
from authentik.admin.utils import get_system_settings
from authentik.crypto.secrets.models import Secret, SecretType, create_named_secret
from authentik.events.models import Event, EventAction


class TestSecret(TestCase):
    """Managed secret behavior."""

    def test_rotate(self):
        secret = Secret.objects.create(name="test")
        previous = secret.secret_value

        value = secret.rotate()

        secret.refresh_from_db()
        self.assertEqual(secret.secret_value, value)
        self.assertNotEqual(value, previous)
        self.assertEqual(len(value), DEFAULT_TOKEN_LENGTH)
        event = Event.objects.get(action=EventAction.SECRET_ROTATE)
        self.assertEqual(event.context["secret"]["pk"], secret.pk.hex)
        self.assertNotIn(value, str(event.context))

    def test_generation_uses_configured_token_length(self):
        settings = get_system_settings()
        settings.default_token_length = 64
        settings.save()
        secret = Secret.objects.create(name="configured")
        self.assertEqual(len(secret.secret_value), 64)
        self.assertRegex(secret.secret_value, r"^[a-zA-Z0-9]+$")

        settings.default_token_length = 80
        settings.save()
        value = secret.rotate()
        self.assertEqual(len(value), 80)
        self.assertRegex(value, r"^[a-zA-Z0-9]+$")

    def test_non_text_cannot_rotate(self):
        secret = Secret.objects.create(name="file", type=SecretType.FILE, secret_value="aGk=")
        with self.assertRaises(ValueError):
            secret.rotate()

    def test_collision_safe_name(self):
        first = create_named_secret("consumer")
        second = create_named_secret("consumer")
        self.assertEqual(first.name, "consumer")
        self.assertEqual(second.name, "consumer (2)")

    def test_json_values(self):
        for value in ['{"token": "value"}', "token: value\n"]:
            with self.subTest(value=value):
                secret = Secret(type=SecretType.JSON, secret_value=value)
                secret.validate_value(value)
                self.assertEqual(secret.get_json(), {"token": "value"})

    def test_invalid_values(self):
        for secret_type, value in [
            (SecretType.JSON, "[]"),
            (SecretType.JSON, "null"),
            (SecretType.JSON, "{broken"),
            (SecretType.JSON, "date: 2026-01-01"),
            (SecretType.FILE, "not base64"),
        ]:
            with self.subTest(type=secret_type, value=value):
                with self.assertRaises(ValidationError):
                    Secret(type=secret_type).validate_value(value)

    def test_only_json_secrets_are_parsed(self):
        with self.assertRaises(ValueError):
            Secret(type=SecretType.TEXT, secret_value="{}").get_json()

    def test_replacing_unchanged_value_does_not_audit_rotation(self):
        secret = Secret.objects.create(name="unchanged", secret_value="current")
        secret.replace_value("current")
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())

    def test_parser_error_does_not_disclose_value(self):
        secret = Secret(type=SecretType.JSON, secret_value="private-credential: [unterminated")
        with self.assertRaises(ValueError) as error:
            secret.get_json()
        self.assertNotIn("private-credential", "".join(format_exception(error.exception)))

    def test_invalid_file_replacement_preserves_value(self):
        secret = Secret.objects.create(name="file", type=SecretType.FILE, secret_value="aGk=")
        with self.assertRaises(ValidationError):
            secret.replace_value("not base64")
        self.assertEqual(secret.secret_value, "aGk=")
        secret.refresh_from_db()
        self.assertEqual(secret.secret_value, "aGk=")
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())

    def test_failed_rotation_keeps_value(self):
        secret = Secret.objects.create(name="rollback", secret_value="old")
        previous_updated = secret.last_updated
        with (
            patch(
                "authentik.crypto.secrets.models.secret_value_changed.send",
                side_effect=RuntimeError("consumer failed"),
            ),
            self.assertRaises(RuntimeError),
        ):
            secret.rotate()
        secret.refresh_from_db()
        self.assertEqual(secret.secret_value, "old")
        self.assertEqual(secret.last_updated, previous_updated)
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())
