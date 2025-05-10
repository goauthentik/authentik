"""Test Monitored tasks"""

# from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

# from authentik.core.tasks import clean_expired_models
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import SystemTask as DBSystemTask
from authentik.events.models import TaskStatus
from authentik.events.system_tasks import SystemTask
from authentik.lib.generators import generate_id
from authentik.root.celery import CELERY_APP


class TestSystemTasks(APITestCase):
    """Test Monitored tasks"""

    def setUp(self):
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_failed_successful_remove_state(self):
        """Test that a task with `save_on_success` set to `False` that failed saves
        a state, and upon successful completion will delete the state"""
        should_fail = True
        uid = generate_id()

        @CELERY_APP.task(
            bind=True,
            base=SystemTask,
        )
        def test_task(self: SystemTask):
            self.save_on_success = False
            self.set_uid(uid)
            self.set_status(TaskStatus.ERROR if should_fail else TaskStatus.SUCCESSFUL)

        # First test successful run
        should_fail = False
        test_task.delay().get()
        self.assertIsNone(DBSystemTask.objects.filter(name="test_task", uid=uid).first())

        # Then test failed
        should_fail = True
        test_task.delay().get()
        task = DBSystemTask.objects.filter(name="test_task", uid=uid).first()
        self.assertEqual(task.status, TaskStatus.ERROR)

        # Then after that, the state should be removed
        should_fail = False
        test_task.delay().get()
        self.assertIsNone(DBSystemTask.objects.filter(name="test_task", uid=uid).first())

    #
    # def test_tasks(self):
    #     """Test Task API"""
    #     clean_expired_models.send()
    #     response = self.client.get(reverse("authentik_api:systemtask-list"))
    #     self.assertEqual(response.status_code, 200)
    #     body = loads(response.content)
    #     self.assertTrue(any(task["name"] == "clean_expired_models" for task in body["results"]))
    #
    # def test_tasks_single(self):
    #     """Test Task API (read single)"""
    #     clean_expired_models.delay().get()
    #     task = DBSystemTask.objects.filter(name="clean_expired_models").first()
    #     response = self.client.get(
    #         reverse(
    #             "authentik_api:systemtask-detail",
    #             kwargs={"pk": str(task.pk)},
    #         )
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     body = loads(response.content)
    #     self.assertEqual(body["status"], TaskStatus.SUCCESSFUL.value)
    #     self.assertEqual(body["name"], "clean_expired_models")
    #     response = self.client.get(
    #         reverse("authentik_api:systemtask-detail", kwargs={"pk": "qwerqwer"})
    #     )
    #     self.assertEqual(response.status_code, 404)
    #
    # def test_tasks_run(self):
    #     """Test Task API (run)"""
    #     clean_expired_models.delay().get()
    #     task = DBSystemTask.objects.filter(name="clean_expired_models").first()
    #     response = self.client.post(
    #         reverse(
    #             "authentik_api:systemtask-run",
    #             kwargs={"pk": str(task.pk)},
    #         )
    #     )
    #     self.assertEqual(response.status_code, 204)

    def test_tasks_run_404(self):
        """Test Task API (run, 404)"""
        response = self.client.post(
            reverse(
                "authentik_api:systemtask-run",
                kwargs={"pk": "qwerqewrqrqewrqewr"},
            )
        )
        self.assertEqual(response.status_code, 404)
