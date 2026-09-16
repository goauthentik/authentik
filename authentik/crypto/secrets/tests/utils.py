"""Helpers for models that reference secrets in tests."""

from authentik.crypto.secrets.models import Secret, SecretType
from authentik.lib.generators import generate_id

KUBECONFIG = """apiVersion: v1
kind: Config
current-context: test
clusters:
- name: test
  cluster:
    server: https://cluster.example.com
contexts:
- name: test
  context:
    cluster: test
    user: test
users:
- name: test
  user:
    token: cluster-token
"""


def create_test_secret(value: str, secret_type: SecretType = SecretType.TEXT) -> Secret:
    """Create a uniquely named secret with a known value."""
    return Secret.objects.create(name=generate_id(), type=secret_type, value=value)
