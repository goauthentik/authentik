"""RBAC role tests"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestRoles(APITestCase):
    """Test roles"""

    def setUp(self) -> None:
        self.login_user = create_test_user()
        self.user = create_test_user()

    def test_role_create(self):
        """Test creation"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.save()
        role.assign_perms("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(self.user)
        self.assertTrue(self.user.has_perm("authentik_core.view_application"))

    def test_role_create_add_reverse(self):
        """Test creation (add user in reverse)"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_perms("authentik_core.view_application")
        group.roles.add(role)
        self.user.groups.add(group)
        self.assertTrue(self.user.has_perm("authentik_core.view_application"))

    def test_remove_group_delete(self):
        """Test creation and remove"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_perms("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(self.user)
        self.assertTrue(self.user.has_perm("authentik_core.view_application"))
        group.delete()
        user = User.objects.get(username=self.user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))

    def test_remove_roles_remove(self):
        """Test assigning permission to role, then removing role from group"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_perms("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(self.user)
        self.assertTrue(self.user.has_perm("authentik_core.view_application"))
        group.roles.remove(role)
        user = User.objects.get(username=self.user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))

    def test_remove_role_delete(self):
        """Test assigning permissions to role, then removing role"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_perms("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(self.user)
        self.assertTrue(self.user.has_perm("authentik_core.view_application"))
        role.delete()
        user = User.objects.get(username=self.user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))

    def test_remove_users_remove(self):
        """Test assigning permission to role, then removing user from group"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_perms("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(self.user)
        self.assertTrue(self.user.has_perm("authentik_core.view_application"))
        group.users.remove(self.user)
        user = User.objects.get(username=self.user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))

    def test_remove_users_remove_reverse(self):
        """Test assigning permission to role, then removing user from group in reverse"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_perms("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(self.user)
        self.assertTrue(self.user.has_perm("authentik_core.view_application"))
        self.user.groups.remove(group)
        user = User.objects.get(username=self.user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))

    def test_add_user_api(self):
        """Test add_user"""
        role = Role.objects.create(name=generate_id())
        self.login_user.assign_perms_to_managed_role("authentik_core.view_user")
        self.login_user.assign_perms_to_managed_role("authentik_rbac.change_role", role)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:roles-add-user", kwargs={"pk": role.pk}),
            data={
                "pk": self.user.pk,
            },
        )
        self.assertEqual(res.status_code, 204)
        role.refresh_from_db()
        self.assertEqual(list(role.users.all()), [self.user])

    def test_add_user_api_404(self):
        """Test add_user"""
        role = Role.objects.create(name=generate_id())
        self.login_user.assign_perms_to_managed_role("authentik_core.view_user")
        self.login_user.assign_perms_to_managed_role("authentik_rbac.change_role", role)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:roles-add-user", kwargs={"pk": role.pk}),
            data={
                "pk": self.user.pk + 3,
            },
        )
        self.assertEqual(res.status_code, 404)

    def test_remove_user_api(self):
        """Test remove_user"""
        role = Role.objects.create(name=generate_id())
        self.login_user.assign_perms_to_managed_role("authentik_core.view_user")
        self.login_user.assign_perms_to_managed_role("authentik_rbac.change_role", role)
        role.users.add(self.user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:roles-remove-user", kwargs={"pk": role.pk}),
            data={
                "pk": self.user.pk,
            },
        )
        self.assertEqual(res.status_code, 204)
        role.refresh_from_db()
        self.assertEqual(list(role.users.all()), [])

    def test_remove_user_404_api(self):
        """Test remove_user"""
        role = Role.objects.create(name=generate_id())
        self.login_user.assign_perms_to_managed_role("authentik_core.view_user")
        self.login_user.assign_perms_to_managed_role("authentik_rbac.change_role", role)
        role.users.add(self.user)
        self.client.force_login(self.login_user)
        res = self.client.post(
            reverse("authentik_api:roles-remove-user", kwargs={"pk": role.pk}),
            data={
                "pk": self.user.pk + 3,
            },
        )
        self.assertEqual(res.status_code, 404)

    def test_user_count_direct(self):
        """Test user_count counts users assigned to a role directly"""
        role = Role.objects.create(name=generate_id())
        self.assertEqual(role.user_count, 0)
        role.users.add(self.user)
        self.assertEqual(role.user_count, 1)

    def test_user_count_group(self):
        """Test user_count counts users that are members of a group with the role"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        group.roles.add(role)
        group.users.add(self.user)
        self.assertEqual(role.user_count, 1)

    def test_user_count_inherited_group(self):
        """Test user_count counts users of a group that inherits the role from an ancestor"""
        parent_group = Group.objects.create(name=generate_id())
        child_group = Group.objects.create(name=generate_id())
        child_group.parents.add(parent_group)
        role = Role.objects.create(name=generate_id())
        parent_group.roles.add(role)
        child_group.users.add(self.user)
        self.assertEqual(role.user_count, 1)

    def test_user_count_distinct(self):
        """Test user_count counts a user once even when assigned directly and via a group"""
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        group.roles.add(role)
        group.users.add(self.user)
        role.users.add(self.user)
        self.assertEqual(role.user_count, 1)

    def test_user_count_api(self):
        """Test user_count is returned by the API"""
        role = Role.objects.create(name=generate_id())
        role.users.add(self.user)
        self.login_user.assign_perms_to_managed_role("authentik_rbac.view_role")
        self.client.force_login(self.login_user)
        res = self.client.get(
            reverse("authentik_api:roles-detail", kwargs={"pk": role.pk}),
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user_count"], 1)
