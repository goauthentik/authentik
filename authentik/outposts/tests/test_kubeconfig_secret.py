"""Kubernetes service connections validate their kubeconfig secret."""

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.crypto.secrets.models import SecretType
from authentik.crypto.secrets.tests.utils import create_test_secret
from authentik.outposts.controllers.kubernetes import KubernetesClient
from authentik.outposts.models import KubernetesServiceConnection

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
INVALID = [
    "clusters: []",
    "current-context: test\ncontexts: {}",
    "current-context: test\ncontexts: [null]",
]


class TestKubeconfigSecret(APITestCase):
    def setUp(self):
        self.client.force_login(create_test_admin_user())
        self.secret = create_test_secret(KUBECONFIG, SecretType.JSON)
        self.connection = KubernetesServiceConnection.objects.create(
            name="kubernetes", kubeconfig_ref=self.secret
        )

    def test_replacement_must_be_a_kubeconfig(self):
        for value in INVALID:
            with self.subTest(value=value):
                response = self.client.patch(
                    reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}),
                    {"value": value},
                )
                self.assertEqual(response.status_code, 400, response.content)
                with self.assertRaises(ValidationError):
                    self.secret.replace_value(value)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.secret_value, KUBECONFIG)

    def test_reference_must_be_a_kubeconfig(self):
        for value in INVALID:
            with self.subTest(value=value):
                response = self.client.post(
                    reverse("authentik_api:kubernetesserviceconnection-list"),
                    {
                        "name": "invalid",
                        "local": False,
                        "kubeconfig_ref": str(create_test_secret(value, SecretType.JSON).pk),
                    },
                )
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn("kubeconfig_ref", response.json())

    def test_client_reads_kubeconfig(self):
        with KubernetesClient(self.connection) as client:
            self.assertEqual(client.configuration.host, "https://cluster.example.com")
            self.assertEqual(client.configuration.api_key["BearerToken"], "Bearer cluster-token")

    def test_local_connection_needs_no_secret(self):
        connection = KubernetesServiceConnection.objects.create(name="local", local=True)
        url = reverse(
            "authentik_api:kubernetesserviceconnection-detail", kwargs={"pk": connection.pk}
        )
        response = self.client.patch(url, {"name": "renamed"})
        self.assertEqual(response.status_code, 200, response.content)
        response = self.client.patch(url, {"local": False})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("kubeconfig_ref", response.json())

    def test_unrelated_update_skips_validation(self):
        """A stored kubeconfig is only checked when the connection's credentials change."""
        with patch("authentik.outposts.api.service_connections.validate_kubeconfig") as validate:
            response = self.client.patch(
                reverse(
                    "authentik_api:kubernetesserviceconnection-detail",
                    kwargs={"pk": self.connection.pk},
                ),
                {"verify_ssl": False},
            )
        self.assertEqual(response.status_code, 200, response.content)
        validate.assert_not_called()

    def test_replacement_refreshes_connection_state(self):
        with (
            patch(
                "authentik.outposts.signals.outpost_service_connection_monitor.send_with_options"
            ) as monitor,
            self.captureOnCommitCallbacks(execute=True),
        ):
            self.secret.replace_value(KUBECONFIG.replace("cluster-token", "new-token"))
        monitor.assert_called_once_with(args=(self.connection.pk,), rel_obj=self.connection)
