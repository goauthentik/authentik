from django.test import TestCase
from django_dramatiq_postgres.models import TaskState
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

    def test_task_deduplicate_by_uid(self):
        """Test opt-in task deduplication by uid"""

        @actor
        def test_task():
            pass

        broker = get_broker()
        worker = broker.worker
        broker.worker = None
        try:
            first = test_task.send_with_options(uid="same", deduplicate_by_uid=True)
            second = test_task.send_with_options(uid="same", deduplicate_by_uid=True)
        finally:
            broker.worker = worker

        self.assertEqual(first.message_id, second.message_id)
        self.assertEqual(
            Task.objects.filter(actor_name=test_task.actor_name, _uid="same").count(),
            1,
        )
        self.assertEqual(
            list(
                TaskLog.objects.filter(task_id=first.message_id)
                .order_by("timestamp")
                .values_list("event", flat=True)
            ),
            ["Task has been queued"],
        )
        del broker.actors[test_task.actor_name]

    def test_task_deduplicate_by_uid_terminal_state(self):
        """Test uid deduplication only considers active tasks"""

        @actor
        def test_task():
            pass

        broker = get_broker()
        worker = broker.worker
        broker.worker = None
        try:
            first = test_task.send_with_options(uid="same", deduplicate_by_uid=True)
            Task.objects.filter(message_id=first.message_id).update(state=TaskState.DONE)
            second = test_task.send_with_options(uid="same", deduplicate_by_uid=True)
        finally:
            broker.worker = worker

        self.assertNotEqual(first.message_id, second.message_id)
        self.assertEqual(
            Task.objects.filter(actor_name=test_task.actor_name, _uid="same").count(),
            2,
        )
        del broker.actors[test_task.actor_name]

    def test_task_uid_without_deduplication(self):
        """Test task uids keep existing behavior without opt-in deduplication"""

        @actor
        def test_task():
            pass

        broker = get_broker()
        worker = broker.worker
        broker.worker = None
        try:
            first = test_task.send_with_options(uid="same")
            second = test_task.send_with_options(uid="same")
        finally:
            broker.worker = worker

        self.assertNotEqual(first.message_id, second.message_id)
        self.assertEqual(
            Task.objects.filter(actor_name=test_task.actor_name, _uid="same").count(),
            2,
        )
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
