"""Managed secret model tests."""

from django.test import TestCase

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
