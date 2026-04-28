from django.test import TestCase
from dramatiq import actor, get_broker

from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task, TaskLog


class TestWorkerMiddleware(TestCase):

    def test_task_log(self):
        @actor
        def test_task():
            self = CurrentTask.get_task()
            self.info("foo")

        test_task.send()
        task = Task.objects.filter(actor_name=test_task.actor_name).first()
        logs = list(
            TaskLog.objects.filter(task=task).order_by("timestamp").values_list("event", flat=True)
        )
        self.assertEqual(
            logs,
            [
                "Task has been queued",
                "Task is being processed",
                "foo",
                "Task finished processing without errors",
            ],
        )
        broker = get_broker()
        del broker.actors[test_task.actor_name]

    def test_task_exceptions(self):
        @actor
        def test_task():
            raise ValueError("foo")

        test_task.send()
        task = Task.objects.filter(actor_name=test_task.actor_name).first()
        logs = list(
            TaskLog.objects.filter(task=task).order_by("timestamp").values_list("event", flat=True)
        )
        self.assertEqual(
            logs,
            [
                "Task has been queued",
                "Task is being processed",
                "foo",
            ],
        )
        broker = get_broker()
        del broker.actors[test_task.actor_name]
