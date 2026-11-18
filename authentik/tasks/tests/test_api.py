from uuid import uuid4

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.timezone import now
from django_dramatiq_postgres.models import TaskState

from authentik.core.models import Group
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.lib.generators import generate_id
from authentik.tasks.models import Task, TaskLog


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

    def _task(self) -> Task:
        task = Task.objects.create(
            message_id=uuid4(), actor_name="test.actor", message=b"\x00", state=TaskState.DONE
        )
        for event, previous in (("current", False), ("previous", True)):
            TaskLog.objects.create(
                task=task,
                event=f"{event} {task.pk}",
                log_level="info",
                logger="test",
                timestamp=now(),
                attributes={},
                previous=previous,
            )
        return task

    def _list(self, tasks: list[Task]) -> tuple[list[dict], int]:
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                reverse("authentik_api:task-list"),
                data={"message_id__in": ",".join(str(task.pk) for task in tasks)},
            )
        self.assertEqual(response.status_code, 200)
        return response.json()["results"], len(queries)

    def test_task_list_logs(self):
        """Test each listed task has its own logs, and listing more tasks runs no more queries"""
        one_task = [self._task()]
        # The first request also sets up the session and caches
        self._list(one_task)
        _, one_task_queries = self._list(one_task)
        tasks = [self._task() for _ in range(3)]
        results, queries = self._list(tasks)
        self.assertEqual(queries, one_task_queries)
        self.assertCountEqual(
            [result["message_id"] for result in results], [str(t.pk) for t in tasks]
        )
        for result in results:
            task = result["message_id"]
            self.assertEqual([log["event"] for log in result["logs"]], [f"current {task}"])
            self.assertEqual(
                [log["event"] for log in result["previous_logs"]], [f"previous {task}"]
            )

    def test_task_list_object_filter(self):
        """Test filtering tasks by the content type and ID of their object"""
        other = create_test_user()
        tasks = []
        for rel_obj in (self.user, self.user, other, Group.objects.create(name=generate_id())):
            task = self._task()
            task.rel_obj = rel_obj
            task.save()
            tasks.append(task)
        for query, expected in (
            ({"rel_obj_content_type__app_label": "authentik_core"}, tasks),
            (
                {
                    "rel_obj_content_type__app_label": "authentik_core",
                    "rel_obj_content_type__model": "user",
                },
                tasks[:3],
            ),
            ({"rel_obj_content_type__model": "user", "rel_obj_id": str(self.user.pk)}, tasks[:2]),
        ):
            with self.subTest(query=query):
                # Creating users and groups may queue other tasks, so only look at these
                query["message_id__in"] = ",".join(str(task.pk) for task in tasks)
                response = self.client.get(reverse("authentik_api:task-list"), data=query)
                self.assertEqual(response.status_code, 200)
                self.assertCountEqual(
                    [result["message_id"] for result in response.json()["results"]],
                    [str(task.pk) for task in expected],
                )
