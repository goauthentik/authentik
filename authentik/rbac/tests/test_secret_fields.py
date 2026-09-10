"""Test secret field exposure in API responses"""

from json import dumps, loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.outposts.models import KubernetesServiceConnection
from authentik.rbac.models import Role
from authentik.secrets.tests.utils import create_test_secret


class TestSecretFields(APITestCase):
    """Consumer APIs expose references, even to administrators."""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

        KubernetesServiceConnection.objects.all().delete()
        self.kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "current-context": "test",
            "clusters": [{"name": "test", "cluster": {"server": "https://localhost"}}],
            "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
            "users": [{"name": "test", "user": {"token": generate_id()}}],
        }
        self.secret = create_test_secret(dumps(self.kubeconfig))
        self.connection = KubernetesServiceConnection.objects.create(
            name=generate_id(), secret=self.secret
        )

    def test_connection_detail_view(self):
        """Test connection detail (role has global view permission)"""
        self.role.assign_perms("authentik_outposts.view_kubernetesserviceconnection")
        self.client.force_login(self.user)

        res = self.client.get(
            reverse(
                "authentik_api:kubernetesserviceconnection-detail",
                kwargs={"pk": self.connection.pk},
            )
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("kubeconfig", body)
        self.assertEqual(body["name"], self.connection.name)

    def test_connection_list_view(self):
        """Test connection list (role has global view permission)"""
        self.role.assign_perms("authentik_outposts.view_kubernetesserviceconnection")
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:kubernetesserviceconnection-list"))
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)
        self.assertNotIn("kubeconfig", body["results"][0])
        self.assertEqual(body["results"][0]["name"], self.connection.name)

    def test_connection_detail_change_global(self):
        """Test connection detail (role has global change permission)"""
        self.role.assign_perms(
            [
                "authentik_outposts.view_kubernetesserviceconnection",
                "authentik_outposts.change_kubernetesserviceconnection",
            ]
        )
        self.client.force_login(self.user)

        res = self.client.get(
            reverse(
                "authentik_api:kubernetesserviceconnection-detail",
                kwargs={"pk": self.connection.pk},
            )
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["secret"], str(self.secret.pk))
        self.assertNotIn(self.secret.value, res.content.decode())

    def test_connection_detail_change_object(self):
        """Test connection detail (role has change permission on the object)"""
        self.role.assign_perms(
            "authentik_outposts.view_kubernetesserviceconnection", obj=self.connection
        )
        self.role.assign_perms(
            "authentik_outposts.change_kubernetesserviceconnection", obj=self.connection
        )
        self.client.force_login(self.user)

        res = self.client.get(
            reverse(
                "authentik_api:kubernetesserviceconnection-detail",
                kwargs={"pk": self.connection.pk},
            )
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["secret"], str(self.secret.pk))
        self.assertNotIn(self.secret.value, res.content.decode())

    def test_connection_detail_superuser(self):
        """Test connection detail (superuser)"""
        self.client.force_login(create_test_admin_user())

        res = self.client.get(
            reverse(
                "authentik_api:kubernetesserviceconnection-detail",
                kwargs={"pk": self.connection.pk},
            )
        )
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["secret"], str(self.secret.pk))
        self.assertNotIn(self.secret.value, res.content.decode())

    def test_connection_create(self):
        """Test connection create (role has global add permission, but no change permission)"""
        self.role.assign_perms("authentik_outposts.add_kubernetesserviceconnection")
        self.client.force_login(self.user)

        name = generate_id()
        secret = create_test_secret(dumps(self.kubeconfig))
        self.role.assign_perms("authentik_secrets.view_secret_value", secret)
        res = self.client.post(
            reverse("authentik_api:kubernetesserviceconnection-list"),
            {
                "name": name,
                "secret": str(secret.pk),
                "local": False,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)
        body = loads(res.content)
        self.assertNotIn("kubeconfig", body)
        connection = KubernetesServiceConnection.objects.get(name=name)
        self.assertEqual(connection.secret, secret)
