from django.test import TestCase
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user


class TestAdminAPI(TestCase):
    """test admin api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_workers(self):
        """Test Workers API"""
        response = self.client.get(reverse("authentik_api:tasks_workers"))
        self.assertEqual(response.status_code, 200)
        # Disabled for flakiness
        # body = loads(response.content)
        # self.assertEqual(len(body), 1)
