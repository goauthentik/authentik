"""Helpers for models that reference secrets in tests."""

from authentik.crypto.secrets.models import Secret, SecretType
from authentik.lib.generators import generate_id


def create_test_secret(value: str, type: SecretType = SecretType.TEXT) -> Secret:
    """Create a uniquely named secret with a known value."""
    return Secret.objects.create(name=generate_id(), type=type, secret_value=value)
