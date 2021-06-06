"""Test Users API"""
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User


class TestUsersAPI(APITestCase):
    """Test Users API"""

    def setUp(self) -> None:
        self.admin = User.objects.get(username="akadmin")
        self.user = User.objects.create(username="test-user")

    def test_metrics(self):
        """Test user's metrics"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("authentik_api:user-metrics", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_metrics_denied(self):
        """Test user's metrics (non-superuser)"""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("authentik_api:user-metrics", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 403)
