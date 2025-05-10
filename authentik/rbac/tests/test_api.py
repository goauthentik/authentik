"""Test RBACPermissionViewSet api"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.crypto.generators import generate_id
from authentik.rbac.models import Role


class TestRBACAPI(APITestCase):
    """Test RBACPermissionViewSet api"""

    def setUp(self) -> None:
        self.superuser = create_test_admin_user()

        self.user = create_test_user()
        self.role = Role.objects.create(name=generate_id())
        self.group = Group.objects.create(name=generate_id())
        self.group.roles.add(self.role)
        self.group.users.add(self.user)

    def test_list(self):
        self.client.force_login(self.superuser)
        res = self.client.get(reverse("authentik_api:permission-list"))
        self.assertEqual(res.status_code, 200)
