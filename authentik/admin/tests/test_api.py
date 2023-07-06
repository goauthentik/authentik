"""test admin api"""
from json import loads

from django.test import TestCase
from django.urls import reverse

from authentik import __version__
from authentik.blueprints.tests import reconcile_app
from authentik.core.models import Group, User
from authentik.core.tasks import clean_expired_models
from authentik.events.monitored_tasks import TaskResultStatus
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

    def test_tasks(self):
        """Test Task API"""
        clean_expired_models.delay()
        response = self.client.get(reverse("authentik_api:admin_system_tasks-list"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertTrue(any(task["task_name"] == "clean_expired_models" for task in body))

    def test_tasks_single(self):
        """Test Task API (read single)"""
        clean_expired_models.delay()
        response = self.client.get(
            reverse(
                "authentik_api:admin_system_tasks-detail",
                kwargs={"pk": "clean_expired_models"},
            )
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["status"], TaskResultStatus.SUCCESSFUL.name)
        self.assertEqual(body["task_name"], "clean_expired_models")
        response = self.client.get(
            reverse("authentik_api:admin_system_tasks-detail", kwargs={"pk": "qwerqwer"})
        )
        self.assertEqual(response.status_code, 404)

    def test_tasks_retry(self):
        """Test Task API (retry)"""
        clean_expired_models.delay()
        response = self.client.post(
            reverse(
                "authentik_api:admin_system_tasks-retry",
                kwargs={"pk": "clean_expired_models"},
            )
        )
        self.assertEqual(response.status_code, 204)

    def test_tasks_retry_404(self):
        """Test Task API (retry, 404)"""
        response = self.client.post(
            reverse(
                "authentik_api:admin_system_tasks-retry",
                kwargs={"pk": "qwerqewrqrqewrqewr"},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_version(self):
        """Test Version API"""
        response = self.client.get(reverse("authentik_api:admin_version"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["version_current"], __version__)

    def test_workers(self):
        """Test Workers API"""
        response = self.client.get(reverse("authentik_api:admin_workers"))
        self.assertEqual(response.status_code, 200)
        body = loads(response.content)
        self.assertEqual(body["count"], 0)

    def test_metrics(self):
        """Test metrics API"""
        response = self.client.get(reverse("authentik_api:admin_metrics"))
        self.assertEqual(response.status_code, 200)

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
