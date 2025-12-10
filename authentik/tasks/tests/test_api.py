from json import loads

from django.test import TestCase
from django.urls import reverse

from authentik.core.models import Group, User
from authentik.lib.generators import generate_id


class TestAdminAPI(TestCase):
    """test admin api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    def test_workers(self):
        """Test Workers API"""
        response = self.client.get(reverse("authentik_api:tasks_workers"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(len(body), 0)
