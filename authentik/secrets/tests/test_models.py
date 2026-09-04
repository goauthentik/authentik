"""Managed secret model tests."""

from django.test import TestCase

from authentik.events.models import Event, EventAction
from authentik.secrets.models import Secret, SecretType, create_named_secret


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
