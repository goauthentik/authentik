"""Test UserAssignedPermissionViewSet api"""
from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Group, UserTypes
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.rbac.api.rbac_assigned_by_users import UserAssignedObjectPermissionSerializer
from authentik.rbac.models import Role
from authentik.stages.invitation.models import Invitation


class TestRBACUserAPI(APITestCase):
    """Test UserAssignedPermissionViewSet api"""

    def setUp(self) -> None:
        self.superuser = create_test_admin_user()

        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

    def test_filter_assigned(self):
        """Test UserAssignedPermissionViewSet's filters"""
        inv = Invitation.objects.create(
            name=generate_id(),
            created_by=self.superuser,
        )
        assign_perm("authentik_stages_invitation.view_invitation", self.user, inv)
        # self.user doesn't have permissions to see their (object) permissions
        self.client.force_login(self.superuser)
        res = self.client.get(
            reverse("authentik_api:permissions-assigned-by-users-list"),
            {
                "model": "authentik_stages_invitation.invitation",
                "object_pk": str(inv.pk),
                "ordering": "pk",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content.decode(),
            {
                "pagination": {
                    "next": 0,
                    "previous": 0,
                    "count": 2,
                    "current": 1,
                    "total_pages": 1,
                    "start_index": 1,
                    "end_index": 2,
                },
                "results": sorted(
                    [
                        UserAssignedObjectPermissionSerializer(instance=self.user).data,
                        UserAssignedObjectPermissionSerializer(instance=self.superuser).data,
                    ],
                    key=lambda u: u["pk"],
                ),
            },
        )

    def test_assign_global(self):
        """Test permission assign"""
        self.client.force_login(self.superuser)
        res = self.client.post(
            reverse(
                "authentik_api:permissions-assigned-by-users-assign",
                kwargs={
                    "pk": self.user.pk,
                },
            ),
            {
                "permissions": ["authentik_stages_invitation.view_invitation"],
            },
        )
        self.assertEqual(res.status_code, 204)
        self.assertTrue(self.user.has_perm("authentik_stages_invitation.view_invitation"))

    def test_assign_global_internal_sa(self):
        """Test permission assign (to internal service account)"""
        self.client.force_login(self.superuser)
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save()
        res = self.client.post(
            reverse(
                "authentik_api:permissions-assigned-by-users-assign",
                kwargs={
                    "pk": self.user.pk,
                },
            ),
            {
                "permissions": ["authentik_stages_invitation.view_invitation"],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertFalse(self.user.has_perm("authentik_stages_invitation.view_invitation"))

    def test_assign_object(self):
        """Test permission assign (object)"""
        inv = Invitation.objects.create(
            name=generate_id(),
            created_by=self.superuser,
        )
        self.client.force_login(self.superuser)
        res = self.client.post(
            reverse(
                "authentik_api:permissions-assigned-by-users-assign",
                kwargs={
                    "pk": self.user.pk,
                },
            ),
            {
                "permissions": ["authentik_stages_invitation.view_invitation"],
                "model": "authentik_stages_invitation.invitation",
                "object_pk": str(inv.pk),
            },
        )
        self.assertEqual(res.status_code, 204)
        self.assertTrue(
            self.user.has_perm(
                "authentik_stages_invitation.view_invitation",
                inv,
            )
        )

    def test_unassign_global(self):
        """Test permission unassign"""
        assign_perm("authentik_stages_invitation.view_invitation", self.user)
        self.client.force_login(self.superuser)
        res = self.client.patch(
            reverse(
                "authentik_api:permissions-assigned-by-users-unassign",
                kwargs={
                    "pk": self.user.pk,
                },
            ),
            {
                "permissions": ["authentik_stages_invitation.view_invitation"],
            },
        )
        self.assertEqual(res.status_code, 204)
        self.assertFalse(self.user.has_perm("authentik_stages_invitation.view_invitation"))

    def test_unassign_global_internal_sa(self):
        """Test permission unassign (from internal service account)"""
        self.client.force_login(self.superuser)
        self.user.type = UserTypes.INTERNAL_SERVICE_ACCOUNT
        self.user.save()
        assign_perm("authentik_stages_invitation.view_invitation", self.user)
        self.client.force_login(self.superuser)
        res = self.client.patch(
            reverse(
                "authentik_api:permissions-assigned-by-users-unassign",
                kwargs={
                    "pk": self.user.pk,
                },
            ),
            {
                "permissions": ["authentik_stages_invitation.view_invitation"],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertTrue(self.user.has_perm("authentik_stages_invitation.view_invitation"))

    def test_unassign_object(self):
        """Test permission unassign (object)"""
        inv = Invitation.objects.create(
            name=generate_id(),
            created_by=self.superuser,
        )
        assign_perm("authentik_stages_invitation.view_invitation", self.user, inv)
        self.client.force_login(self.superuser)
        res = self.client.patch(
            reverse(
                "authentik_api:permissions-assigned-by-users-unassign",
                kwargs={
                    "pk": self.user.pk,
                },
            ),
            {
                "permissions": ["authentik_stages_invitation.view_invitation"],
                "model": "authentik_stages_invitation.invitation",
                "object_pk": str(inv.pk),
            },
        )
        self.assertEqual(res.status_code, 204)
        self.assertFalse(
            self.user.has_perm(
                "authentik_stages_invitation.view_invitation",
                inv,
            )
        )
