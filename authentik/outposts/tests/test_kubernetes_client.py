"""Kubernetes client tests"""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from authentik.outposts.controllers.kubernetes import KubernetesClient
from authentik.outposts.models import KubernetesServiceConnection, ServiceConnectionInvalid


class TestKubernetesClient(TestCase):
    """Kubeconfig loading"""

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.marker = self.directory / "marker"

    def test_token_valid(self):
        connection = KubernetesServiceConnection(
            kubeconfig={
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster", "cluster": {"server": "https://kubernetes.invalid"}}
                ],
                "contexts": [
                    {"name": "context", "context": {"cluster": "cluster", "user": "user"}}
                ],
                "current-context": "context",
                "users": [{"name": "user", "user": {"token": "token"}}],
            }
        )
        client = KubernetesClient(connection)
        self.assertEqual(client.configuration.host, "https://kubernetes.invalid")

    def test_other_context_exec_valid(self):
        connection = KubernetesServiceConnection(
            kubeconfig={
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster", "cluster": {"server": "https://kubernetes.invalid"}},
                    {"name": "other", "cluster": {"server": "https://other.invalid"}},
                ],
                "contexts": [
                    {"name": "context", "context": {"cluster": "cluster", "user": "user"}},
                    {"name": "other", "context": {"cluster": "other", "user": "other"}},
                ],
                "current-context": "context",
                "users": [
                    {"name": "user", "user": {"token": "token"}},
                    {
                        "name": "other",
                        "user": {
                            "exec": {
                                "apiVersion": "client.authentication.k8s.io/v1",
                                "command": "touch",
                                "args": [str(self.marker)],
                            }
                        },
                    },
                ],
            }
        )
        client = KubernetesClient(connection)
        self.assertFalse(self.marker.exists())
        self.assertEqual(client.configuration.host, "https://kubernetes.invalid")

    def test_exec_invalid(self):
        connection = KubernetesServiceConnection(
            kubeconfig={
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster", "cluster": {"server": "https://kubernetes.invalid"}}
                ],
                "contexts": [
                    {"name": "context", "context": {"cluster": "cluster", "user": "user"}}
                ],
                "current-context": "context",
                "users": [
                    {
                        "name": "user",
                        "user": {
                            "exec": {
                                "apiVersion": "client.authentication.k8s.io/v1",
                                "command": "touch",
                                "args": [str(self.marker)],
                            }
                        },
                    }
                ],
            }
        )
        with self.assertRaises(ServiceConnectionInvalid):
            KubernetesClient(connection)
        self.assertFalse(self.marker.exists())

    def test_cmd_path_invalid(self):
        connection = KubernetesServiceConnection(
            kubeconfig={
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster", "cluster": {"server": "https://kubernetes.invalid"}}
                ],
                "contexts": [
                    {"name": "context", "context": {"cluster": "cluster", "user": "user"}}
                ],
                "current-context": "context",
                "users": [
                    {
                        "name": "user",
                        "user": {
                            "auth-provider": {
                                "name": "gcp",
                                "config": {"cmd-path": "touch", "cmd-args": str(self.marker)},
                            }
                        },
                    }
                ],
            }
        )
        with self.assertRaises(ServiceConnectionInvalid):
            KubernetesClient(connection)
        self.assertFalse(self.marker.exists())

    def test_auth_provider_invalid(self):
        connection = KubernetesServiceConnection(
            kubeconfig={
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster", "cluster": {"server": "https://kubernetes.invalid"}}
                ],
                "contexts": [
                    {"name": "context", "context": {"cluster": "cluster", "user": "user"}}
                ],
                "current-context": "context",
                "users": [{"name": "user", "user": {"auth-provider": {"name": "gcp"}}}],
            }
        )
        with self.assertRaises(ServiceConnectionInvalid):
            KubernetesClient(connection)

    def test_token_file_invalid(self):
        token_file = self.directory / "token"
        token_file.write_text("token")
        connection = KubernetesServiceConnection(
            kubeconfig={
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [
                    {"name": "cluster", "cluster": {"server": "https://kubernetes.invalid"}}
                ],
                "contexts": [
                    {"name": "context", "context": {"cluster": "cluster", "user": "user"}}
                ],
                "current-context": "context",
                "users": [{"name": "user", "user": {"tokenFile": str(token_file)}}],
            }
        )
        with self.assertRaises(ServiceConnectionInvalid):
            KubernetesClient(connection)
