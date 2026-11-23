"""Test RBAC tasks"""

from guardian.models import RoleModelPermission, RoleObjectPermission
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.rbac.models import Role
from authentik.rbac.tasks import clean_orphaned_object_permissions


class TestRBACTasks(APITestCase):
    """Test RBAC tasks"""

    def setUp(self) -> None:
        super().setUp()
        self.superuser = create_test_admin_user()
        self.role = Role.objects.create(name=generate_id())

    def test_clean_orphaned_object_permissions(self):
        """Test that object permissions of deleted objects are removed"""
        deleted = Role.objects.create(name=generate_id())
        kept = Role.objects.create(name=generate_id())
        self.role.assign_perms("authentik_rbac.view_role", obj=deleted)
        self.role.assign_perms("authentik_rbac.view_role", obj=kept)
        self.role.assign_perms("authentik_rbac.view_role")
        deleted_pk = str(deleted.pk)
        deleted.delete()

        clean_orphaned_object_permissions.send()

        self.assertFalse(RoleObjectPermission.objects.filter(object_pk=deleted_pk).exists())
        self.assertTrue(RoleObjectPermission.objects.filter(object_pk=str(kept.pk)).exists())
        self.assertTrue(
            RoleModelPermission.objects.filter(
                role=self.role,
                permission__codename="view_role",
            ).exists()
        )
