"""Kubernetes service connection API tests"""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.outposts.models import KubernetesServiceConnection


class TestKubernetesServiceConnectionAPI(APITestCase):
    """Kubeconfig validation"""

    def setUp(self):
        self.client.force_login(create_test_admin_user())
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.marker = self.directory / "marker"

    def test_create_token_valid(self):
        response = self.client.post(
            reverse("authentik_api:kubernetesserviceconnection-list"),
            data={
                "name": generate_id(),
                "kubeconfig": {
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
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_create_other_context_exec_valid(self):
        response = self.client.post(
            reverse("authentik_api:kubernetesserviceconnection-list"),
            data={
                "name": generate_id(),
                "kubeconfig": {
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
                },
            },
            format="json",
        )
        self.assertFalse(self.marker.exists())
        self.assertEqual(response.status_code, 201)

    def test_create_exec_invalid(self):
        response = self.client.post(
            reverse("authentik_api:kubernetesserviceconnection-list"),
            data={
                "name": generate_id(),
                "kubeconfig": {
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
                },
            },
            format="json",
        )
        self.assertFalse(self.marker.exists())
        self.assertEqual(response.status_code, 400)

    def test_create_cmd_path_invalid(self):
        response = self.client.post(
            reverse("authentik_api:kubernetesserviceconnection-list"),
            data={
                "name": generate_id(),
                "kubeconfig": {
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
                },
            },
            format="json",
        )
        self.assertFalse(self.marker.exists())
        self.assertEqual(response.status_code, 400)

    def test_create_auth_provider_invalid(self):
        response = self.client.post(
            reverse("authentik_api:kubernetesserviceconnection-list"),
            data={
                "name": generate_id(),
                "kubeconfig": {
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
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_token_file_invalid(self):
        token_file = self.directory / "token"
        token_file.write_text("token")
        response = self.client.post(
            reverse("authentik_api:kubernetesserviceconnection-list"),
            data={
                "name": generate_id(),
                "kubeconfig": {
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
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_update_exec_invalid(self):
        connection = KubernetesServiceConnection.objects.create(
            name=generate_id(), local=True, kubeconfig={}
        )
        response = self.client.patch(
            reverse(
                "authentik_api:kubernetesserviceconnection-detail", kwargs={"pk": connection.pk}
            ),
            data={
                "kubeconfig": {
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
                },
            },
            format="json",
        )
        self.assertFalse(self.marker.exists())
        self.assertEqual(response.status_code, 400)
