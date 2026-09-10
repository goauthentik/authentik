"""Structured credentials reach their consumers without exposing values in metadata."""

from base64 import b64encode
from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.stages.authenticator_endpoint_gdtc.models import (
    AuthenticatorEndpointGDTCStage,
)
from authentik.outposts.api.service_connections import KubernetesServiceConnectionSerializer
from authentik.outposts.controllers.kubernetes import KubernetesClient
from authentik.outposts.models import KubernetesServiceConnection
from authentik.secrets.api import SecretSerializer
from authentik.secrets.models import Secret, SecretType

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


class TestStructuredSecrets(TestCase):
    def test_google_credentials(self):
        for Model in [
            GoogleWorkspaceProvider,
            GoogleChromeConnector,
            AuthenticatorEndpointGDTCStage,
        ]:
            with self.subTest(model=Model.__name__):
                secret = Secret(
                    type=SecretType.FILE, value=b64encode(b'{"token":"value"}').decode()
                )
                consumer = Model(secret=secret)
                with patch(f"{Model.__module__}.Credentials.from_service_account_info") as factory:
                    consumer.google_credentials()
                self.assertEqual(factory.call_args.args[0], {"token": "value"})

    def test_invalid_structured_value(self):
        field = GoogleChromeConnector().serializer().fields["secret"]
        for secret_type, value in [
            (SecretType.TEXT, "[]"),
            (SecretType.TEXT, "null"),
            (SecretType.TEXT, "password"),
            (SecretType.TEXT, "{broken"),
            (SecretType.TEXT, "!!python/object:os.system {}"),
            (SecretType.FILE, "not base64"),
        ]:
            with self.subTest(type=secret_type, value=value):
                secret = Secret.objects.create(name=value, type=secret_type, value=value)
                with self.assertRaises(ValidationError):
                    field.run_validation(str(secret.pk))

    def test_invalid_structured_replacement(self):
        secret = Secret.objects.create(name="credentials", value='{"token":"value"}')
        GoogleChromeConnector.objects.create(name="connector", secret=secret)
        serializer = SecretSerializer(instance=secret, data={"value": "[]"}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("value", serializer.errors)

    def test_kubeconfig_text_and_file(self):
        for secret_type in [SecretType.MULTILINE, SecretType.FILE]:
            with self.subTest(type=secret_type):
                value = (
                    b64encode(KUBECONFIG.encode()).decode()
                    if secret_type == SecretType.FILE
                    else KUBECONFIG
                )
                secret = Secret.objects.create(name=secret_type, type=secret_type, value=value)
                serializer = KubernetesServiceConnectionSerializer(
                    data={"name": secret_type, "local": False, "secret": str(secret.pk)}
                )
                self.assertTrue(serializer.is_valid(), serializer.errors)
                connection = serializer.save()
                self.assertNotIn("kubeconfig", serializer.data)
                with KubernetesClient(connection) as client:
                    self.assertEqual(client.configuration.host, "https://cluster.example.com")
                    self.assertEqual(
                        client.configuration.api_key["BearerToken"], "Bearer cluster-token"
                    )

    def test_local_connection_needs_no_secret(self):
        connection = KubernetesServiceConnection(name="local", local=True)
        serializer = KubernetesServiceConnectionSerializer(
            instance=connection, data={"name": "renamed"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer = KubernetesServiceConnectionSerializer(
            instance=connection, data={"local": False}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("secret", serializer.errors)

    def test_invalid_current_kubeconfig(self):
        secret = Secret.objects.create(name="invalid", value="not a kubeconfig")
        connection = KubernetesServiceConnection(name="remote", local=False, secret=secret)
        serializer = KubernetesServiceConnectionSerializer(
            instance=connection, data={"name": "renamed"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("secret", serializer.errors)
