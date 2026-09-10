"""Test write-only field exposure in API responses"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role
from authentik.secrets.models import Secret


class TestWriteOnlyFields(APITestCase):
    """Test that write-only fields are never rendered, whatever the caller holds"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

        self.value = generate_id()
        self.secret = Secret.objects.create(
            name=generate_id(),
            value=self.value,
        )

    def test_secret_detail_view(self):
        """Test secret detail (role has global view permission)"""
        self.role.assign_perms("authentik_secrets.view_secret")
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}))
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("value", body)
        self.assertEqual(body["name"], self.secret.name)

    def test_secret_list_view(self):
        """Test secret list (role has global view permission)"""
        self.role.assign_perms("authentik_secrets.view_secret")
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:secret-list"), {"name": self.secret.name})
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertEqual(body["pagination"]["count"], 1)
        self.assertNotIn("value", body["results"][0])
        self.assertEqual(body["results"][0]["name"], self.secret.name)

    def test_secret_detail_change_global(self):
        """Test secret detail (role has global change permission)"""
        self.role.assign_perms(
            [
                "authentik_secrets.view_secret",
                "authentik_secrets.change_secret",
            ]
        )
        self.client.force_login(self.user)

        res = self.client.get(reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}))
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("value", body)

    def test_secret_detail_superuser(self):
        """Test secret detail (superuser)"""
        self.client.force_login(create_test_admin_user())

        res = self.client.get(reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}))
        self.assertEqual(res.status_code, 200)
        body = loads(res.content)
        self.assertNotIn("value", body)

    def test_secret_create(self):
        """Test secret create (the response omits the values that were stored)"""
        self.role.assign_perms("authentik_secrets.add_secret")
        self.client.force_login(self.user)

        name = generate_id()
        value = generate_id()
        res = self.client.post(
            reverse("authentik_api:secret-list"),
            {
                "name": name,
                "value": value,
            },
        )
        self.assertEqual(res.status_code, 201)
        body = loads(res.content)
        self.assertNotIn("value", body)
        secret = Secret.objects.get(name=name)
        self.assertEqual(secret.value, value)

    def test_secret_partial_update_keeps_values(self):
        """Test secret partial update without the write-only fields (as the admin UI sends it)"""
        self.client.force_login(create_test_admin_user())

        name = generate_id()
        res = self.client.patch(
            reverse("authentik_api:secret-detail", kwargs={"pk": self.secret.pk}),
            {"name": name},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.secret.refresh_from_db()
        self.assertEqual(self.secret.name, name)
        self.assertEqual(self.secret.value, self.value)
