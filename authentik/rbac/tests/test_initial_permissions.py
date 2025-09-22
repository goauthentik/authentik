"""Test InitialPermissions"""

from django.contrib.auth.models import Permission
from guardian.shortcuts import assign_perm
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import InitialPermissions, InitialPermissionsMode, Role
from authentik.stages.dummy.models import DummyStage


class TestInitialPermissions(APITestCase):
    """Test InitialPermissions"""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.same_role_user = create_test_user()
        self.different_role_user = create_test_user()

        self.role = Role.objects.create(name=generate_id())
        self.different_role = Role.objects.create(name=generate_id())

        self.group = Group.objects.create(name=generate_id())
        self.different_group = Group.objects.create(name=generate_id())

        self.group.roles.add(self.role)
        self.group.users.add(self.user, self.same_role_user)
        self.different_group.roles.add(self.different_role)
        self.different_group.users.add(self.different_role_user)

        self.ip = InitialPermissions.objects.create(
            name=generate_id(), mode=InitialPermissionsMode.USER, role=self.role
        )
        self.view_role = Permission.objects.filter(codename="view_role").first()
        self.ip.permissions.add(self.view_role)

        assign_perm("authentik_rbac.add_role", self.user)
        self.client.force_login(self.user)

    def test_different_role(self):
        """InitialPermissions for different role does nothing"""
        self.ip.role = self.different_role
        self.ip.save()

        self.client.post(reverse("authentik_api:roles-list"), {"name": "test-role"})

        role = Role.objects.filter(name="test-role").first()
        self.assertFalse(self.user.has_perm("authentik_rbac.view_role", role))

    def test_different_model(self):
        """InitialPermissions for different model does nothing"""
        assign_perm("authentik_stages_dummy.add_dummystage", self.user)

        self.client.post(
            reverse("authentik_api:stages-dummy-list"), {"name": "test-stage", "throw-error": False}
        )

        role = Role.objects.filter(name="test-role").first()
        self.assertFalse(self.user.has_perm("authentik_rbac.view_role", role))
        stage = DummyStage.objects.filter(name="test-stage").first()
        self.assertFalse(self.user.has_perm("authentik_stages_dummy.view_dummystage", stage))

    def test_mode_user(self):
        """InitialPermissions adds user permission in user mode"""
        self.client.post(reverse("authentik_api:roles-list"), {"name": "test-role"})

        role = Role.objects.filter(name="test-role").first()
        self.assertTrue(self.user.has_perm("authentik_rbac.view_role", role))
        self.assertFalse(self.same_role_user.has_perm("authentik_rbac.view_role", role))

    def test_mode_role(self):
        """InitialPermissions adds role permission in role mode"""
        self.ip.mode = InitialPermissionsMode.ROLE
        self.ip.save()

        self.client.post(reverse("authentik_api:roles-list"), {"name": "test-role"})

        role = Role.objects.filter(name="test-role").first()
        self.assertTrue(self.user.has_perm("authentik_rbac.view_role", role))
        self.assertTrue(self.same_role_user.has_perm("authentik_rbac.view_role", role))

    def test_many_permissions(self):
        """InitialPermissions can add multiple permissions"""
        change_role = Permission.objects.filter(codename="change_role").first()
        self.ip.permissions.add(change_role)

        self.client.post(reverse("authentik_api:roles-list"), {"name": "test-role"})

        role = Role.objects.filter(name="test-role").first()
        self.assertTrue(self.user.has_perm("authentik_rbac.view_role", role))
        self.assertTrue(self.user.has_perm("authentik_rbac.change_role", role))

    def test_permissions_separated_by_role(self):
        """When the triggering user is part of two different roles with InitialPermissions in role
        mode, it only adds permissions to the relevant role."""
        self.ip.mode = InitialPermissionsMode.ROLE
        self.ip.save()
        different_ip = InitialPermissions.objects.create(
            name=generate_id(), mode=InitialPermissionsMode.ROLE, role=self.different_role
        )
        change_role = Permission.objects.filter(codename="change_role").first()
        different_ip.permissions.add(change_role)
        self.different_group.users.add(self.user)

        self.client.post(reverse("authentik_api:roles-list"), {"name": "test-role"})

        role = Role.objects.filter(name="test-role").first()
        self.assertTrue(self.user.has_perm("authentik_rbac.view_role", role))
        self.assertTrue(self.same_role_user.has_perm("authentik_rbac.view_role", role))
        self.assertFalse(self.different_role_user.has_perm("authentik_rbac.view_role", role))
        self.assertTrue(self.user.has_perm("authentik_rbac.change_role", role))
        self.assertFalse(self.same_role_user.has_perm("authentik_rbac.change_role", role))
        self.assertTrue(self.different_role_user.has_perm("authentik_rbac.change_role", role))
