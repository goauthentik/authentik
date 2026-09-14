"""Helpers for models that reference secrets in tests."""

from authentik.crypto.secrets.models import Secret
from authentik.lib.generators import generate_id


def create_test_secret(value: str) -> Secret:
    """Create a uniquely named text secret with a known value."""
    return Secret.objects.create(name=generate_id(), value=value)
