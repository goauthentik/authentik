"""Test UserPermissionViewSet api"""

from django.urls import reverse
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.crypto.generators import generate_id
from authentik.rbac.models import Role
from authentik.stages.invitation.models import Invitation


class TestRBACPermissionUsers(APITestCase):
    """Test UserPermissionViewSet api"""

    def setUp(self) -> None:
        self.superuser = create_test_admin_user()

        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

    def test_list(self):
        """Test list of all permissions"""
        self.client.force_login(self.superuser)
        inv = Invitation.objects.create(
            name=generate_id(),
            created_by=self.superuser,
        )
        assign_perm("authentik_stages_invitation.view_invitation", self.user, inv)
        res = self.client.get(reverse("authentik_api:permissions-users-list"))
        self.assertEqual(res.status_code, 200)

    def test_list_role(self):
        """Test list of all permissions"""
        self.client.force_login(self.superuser)
        inv = Invitation.objects.create(
            name=generate_id(),
            created_by=self.superuser,
        )
        assign_perm("authentik_stages_invitation.view_invitation", self.user, inv)
        res = self.client.get(
            reverse("authentik_api:permissions-users-list") + f"?user_id={self.user.pk}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content,
            {
                "pagination": {
                    "next": 0,
                    "previous": 0,
                    "count": 1,
                    "current": 1,
                    "total_pages": 1,
                    "start_index": 1,
                    "end_index": 1,
                },
                "results": [
                    {
                        "id": UserObjectPermission.objects.filter(object_pk=inv.pk).first().pk,
                        "codename": "view_invitation",
                        "model": "invitation",
                        "app_label": "authentik_stages_invitation",
                        "object_pk": str(inv.pk),
                        "name": "Can view Invitation",
                        "app_label_verbose": "authentik Stages.Invitation",
                        "model_verbose": "Invitation",
                        "object_description": str(inv),
                    }
                ],
            },
        )
