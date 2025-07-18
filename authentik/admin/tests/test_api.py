"""test admin api"""

from json import loads

from django.test import TestCase
from django.urls import reverse

from authentik import __version__
from authentik.blueprints.tests import reconcile_app
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

    def test_version(self):
        """Test Version API"""
        response = self.client.get(reverse("authentik_api:admin_version"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["version_current"], __version__)

    def test_apps(self):
        """Test apps API"""
        response = self.client.get(reverse("authentik_api:apps-list"))
        self.assertEqual(response.status_code, 200)

    def test_models(self):
        """Test models API"""
        response = self.client.get(reverse("authentik_api:models-list"))
        self.assertEqual(response.status_code, 200)

    @reconcile_app("authentik_outposts")
    def test_system(self):
        """Test system API"""
        response = self.client.get(reverse("authentik_api:admin_system"))
        self.assertEqual(response.status_code, 200)
