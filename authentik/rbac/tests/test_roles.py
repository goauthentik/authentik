"""RBAC role tests"""
from rest_framework.test import APITestCase

from authentik.core.models import Group, Role
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id


class TestRoles(APITestCase):
    """Test roles"""

    def test_role_create(self):
        """Test creation"""
        user = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])

    def test_role_create_remove(self):
        """Test creation and remove"""
        user = create_test_admin_user()
        group = Group.objects.create(name=generate_id())
        role = Role.objects.create(name=generate_id())
        group.roles.add(role)
        group.users.add(user)
        self.assertEqual(list(role.group.user_set.all()), [user])
        user.delete()
        self.assertEqual(list(role.group.user_set.all()), [])
