from django.test import TestCase
from dramatiq import actor, get_broker, set_broker

from authentik.tasks.middleware import CurrentTask, MetricsMiddleware
from authentik.tasks.models import Task, TaskLog
from authentik.tasks.test import use_test_broker


class TestWorkerMiddleware(TestCase):

    def test_metrics_multiple_brokers(self):
        """Booting another test broker (as e2e tests do per test) must not fail metrics setup"""
        old_broker = get_broker()
        try:
            broker = use_test_broker()
            metrics = next(m for m in broker.middleware if isinstance(m, MetricsMiddleware))
            self.assertTrue(hasattr(metrics, "in_progress_messages"))
            broker.close()
        finally:
            set_broker(old_broker)

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
        @actor(description="test-helper-exception")
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
                "Task has encountered an error: foo",
            ],
        )
        broker = get_broker()
        del broker.actors[test_task.actor_name]
