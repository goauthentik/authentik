"""Structured credentials reach their consumers without exposing values in metadata."""

from base64 import b64encode
from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.crypto.secrets.api import SecretSerializer
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.crypto.secrets.tests.utils import KUBECONFIG
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.stages.authenticator_endpoint_gdtc.models import (
    AuthenticatorEndpointGDTCStage,
)
from authentik.outposts.api.service_connections import KubernetesServiceConnectionSerializer
from authentik.outposts.controllers.kubernetes import KubernetesClient
from authentik.outposts.models import KubernetesServiceConnection


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
                consumer = Model(credentials_ref=secret)
                with patch(f"{Model.__module__}.Credentials.from_service_account_info") as factory:
                    consumer.google_credentials()
                self.assertEqual(factory.call_args.args[0], {"token": "value"})

    def test_invalid_structured_value(self):
        field = GoogleChromeConnector().serializer().fields["credentials_ref"]
        for secret_type, value in [
            (SecretType.MULTILINE, "[]"),
            (SecretType.MULTILINE, "null"),
            (SecretType.MULTILINE, "password"),
            (SecretType.MULTILINE, "{broken"),
            (SecretType.MULTILINE, "!!python/object:os.system {}"),
            (SecretType.FILE, "not base64"),
        ]:
            with self.subTest(type=secret_type, value=value):
                secret = Secret.objects.create(name=value, type=secret_type, value=value)
                with self.assertRaises(ValidationError):
                    field.run_validation(str(secret.pk))

    def test_invalid_structured_replacement(self):
        secret = Secret.objects.create(
            name="credentials", type=SecretType.MULTILINE, value='{"token":"value"}'
        )
        GoogleChromeConnector.objects.create(name="connector", credentials_ref=secret)
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
                    data={"name": secret_type, "local": False, "kubeconfig_ref": str(secret.pk)}
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
        self.assertIn("kubeconfig_ref", serializer.errors)

    def test_invalid_current_kubeconfig(self):
        secret = Secret.objects.create(
            name="invalid", type=SecretType.MULTILINE, value="not a kubeconfig"
        )
        connection = KubernetesServiceConnection(name="remote", local=False, kubeconfig_ref=secret)
        serializer = KubernetesServiceConnectionSerializer(
            instance=connection, data={"name": "renamed"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("kubeconfig_ref", serializer.errors)
