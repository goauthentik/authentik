"""Status codes of API authorization decisions"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestAPIStatus(APITestCase):
    """Hidden objects are 404, or 403 when nothing of the kind is visible at all"""

    def setUp(self):
        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.user.roles.add(self.role)
        self.group = Group.objects.create(name=generate_id())
        self.member = create_test_user()
        self.client.force_login(self.user)

    def group_url(self, group: Group, action: str = "detail") -> str:
        return reverse(f"authentik_api:group-{action}", kwargs={"pk": group.pk})

    def test_detail_nothing_visible(self):
        self.assertEqual(self.client.get(self.group_url(self.group)).status_code, 403)

    def test_detail_other_object_visible(self):
        self.role.assign_perms("authentik_core.view_group", Group.objects.create(name="x"))
        self.assertEqual(self.client.get(self.group_url(self.group)).status_code, 404)

    def test_detail_object_visible(self):
        self.role.assign_perms("authentik_core.view_group", self.group)
        self.assertEqual(self.client.get(self.group_url(self.group)).status_code, 200)

    def test_detail_visible_but_not_changeable(self):
        self.role.assign_perms("authentik_core.view_group", self.group)
        response = self.client.patch(self.group_url(self.group), {"name": generate_id()})
        self.assertEqual(response.status_code, 403)

    def test_add_user_without_permission(self):
        response = self.client.post(self.group_url(self.group, "add-user"), {"pk": "invalid"})
        self.assertEqual(response.status_code, 403)

    def test_add_user_invalid_body(self):
        self.role.assign_perms("authentik_core.add_user_to_group", self.group)
        response = self.client.post(self.group_url(self.group, "add-user"), {"pk": "invalid"})
        self.assertEqual(response.status_code, 400)

    def test_add_user_hidden_user(self):
        self.role.assign_perms("authentik_core.add_user_to_group", self.group)
        response = self.client.post(self.group_url(self.group, "add-user"), {"pk": self.member.pk})
        self.assertEqual(response.status_code, 404)

    def test_add_user_visible_user(self):
        self.role.assign_perms("authentik_core.add_user_to_group", self.group)
        self.role.assign_perms("authentik_core.view_user", self.member)
        response = self.client.post(self.group_url(self.group, "add-user"), {"pk": self.member.pk})
        self.assertEqual(response.status_code, 204)
        self.assertTrue(self.group.users.filter(pk=self.member.pk).exists())
