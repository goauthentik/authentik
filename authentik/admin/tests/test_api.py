"""test admin api"""
from json import loads

from django.shortcuts import reverse
from django.test import TestCase

from authentik import __version__
from authentik.core.models import Group, User


class TestAdminAPI(TestCase):
    """test admin api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username="test-user")
        self.group = Group.objects.create(name="superusers", is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    def test_overview(self):
        """Test Overview API"""
        response = self.client.get(reverse("authentik_api:admin_overview-list"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["version"], __version__)

    def test_metrics(self):
        """Test metrics API"""
        response = self.client.get(reverse("authentik_api:admin_metrics-list"))
        self.assertEqual(response.status_code, 200)

    def test_tasks(self):
        """Test tasks metrics API"""
        response = self.client.get(reverse("authentik_api:admin_system_tasks-list"))
        self.assertEqual(response.status_code, 200)
