"""RBAC role tests"""
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestRoles(APITestCase):
    """Test roles"""

    def test_role_create(self):
        """Test creation"""
        user = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        assign_perm("authentik_core.view_application", role.group)
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))

    def test_role_create_remove(self):
        """Test creation and remove"""
        user = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        assign_perm("authentik_core.view_application", role.group)
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        self.assertTrue(user.has_perm("authentik_core.view_application"))
        user.delete()
        self.assertEqual(list(role.group.user_set.all()), [])
