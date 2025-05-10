"""RBAC role tests"""

from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.crypto.generators import generate_id
from authentik.rbac.models import Role


class TestRoles(APITestCase):
    """Test roles"""

    def test_role_create(self):
        """Test creation"""
        user = create_test_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.save()
        role.assign_permission("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))

    def test_role_create_add_reverse(self):
        """Test creation (add user in reverse)"""
        user = create_test_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_permission("authentik_core.view_application")
        group.roles.add(role)
        user.ak_groups.add(group)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))

    def test_remove_group_delete(self):
        """Test creation and remove"""
        user = create_test_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_permission("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))
        group.delete()
        user = User.objects.get(username=user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))
        self.assertEqual(list(role.group.user_set.all()), [])

    def test_remove_roles_remove(self):
        """Test assigning permission to role, then removing role from group"""
        user = create_test_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_permission("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))
        group.roles.remove(role)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))
        self.assertEqual(list(role.group.user_set.all()), [])

    def test_remove_role_delete(self):
        """Test assigning permissions to role, then removing role"""
        user = create_test_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_permission("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))
        role.delete()
        user = User.objects.get(username=user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))
        self.assertEqual(list(role.group.user_set.all()), [])

    def test_role_assign_twice(self):
        """Test assigning role to two groups"""
        group1 = Group.objects.create(name=generate_id())
        group2 = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_permission("authentik_core.view_application")
        group1.roles.add(role)
        with self.assertRaises(ValidationError):
            group2.roles.add(role)

    def test_remove_users_remove(self):
        """Test assigning permission to role, then removing user from group"""
        user = create_test_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_permission("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))
        group.users.remove(user)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))
        self.assertEqual(list(role.group.user_set.all()), [])

    def test_remove_users_remove_reverse(self):
        """Test assigning permission to role, then removing user from group in reverse"""
        user = create_test_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        role.assign_permission("authentik_core.view_application")
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))
        user.ak_groups.remove(group)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.has_perm("authentik_core.view_application"))
        self.assertEqual(list(role.group.user_set.all()), [])
