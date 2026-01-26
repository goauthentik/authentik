"""Test UI Permissions API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role


class TestUIPermissionsAPI(APITestCase):
    """Test UI Permissions API"""

    def setUp(self) -> None:
        self.superuser = create_test_admin_user()
        self.regular_user = create_test_user()

        # Create a role with limited permissions
        self.limited_role = Role.objects.create(name=generate_id())
        self.limited_role.assign_perms(
            [
                "authentik_core.view_application",
                "authentik_core.view_user",
            ]
        )

        # Create a group and assign the role
        self.limited_group = Group.objects.create(name=generate_id())
        self.limited_group.roles.add(self.limited_role)
        self.regular_user.ak_groups.add(self.limited_group)

    def test_superuser_permissions(self):
        """Test that superuser gets all permissions"""
        self.client.force_login(self.superuser)
        res = self.client.get(reverse("authentik_api:admin_ui_permissions"))
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Superuser should have access to most things
        self.assertTrue(data["can_view_admin_overview"])
        self.assertTrue(data["can_view_applications"])
        self.assertTrue(data["can_view_users"])

    def test_limited_user_permissions(self):
        """Test that limited user gets filtered permissions"""
        self.client.force_login(self.regular_user)
        res = self.client.get(reverse("authentik_api:admin_ui_permissions"))
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Should have overview access (always shown)
        self.assertTrue(data["can_view_admin_overview"])

        # Should have permissions based on role
        self.assertTrue(data["can_view_applications"])
        self.assertTrue(data["can_view_users"])

        # Should NOT have other permissions
        self.assertFalse(data["can_view_policies"])
        self.assertFalse(data["can_view_flows"])

    def test_unauthenticated_denied(self):
        """Test that unauthenticated users are denied"""
        res = self.client.get(reverse("authentik_api:admin_ui_permissions"))
        self.assertEqual(res.status_code, 403)
