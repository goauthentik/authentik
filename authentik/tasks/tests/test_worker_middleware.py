from django.test import TestCase
from dramatiq import actor, get_broker

from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task, TaskLog
from authentik.tasks.schedules.common import ScheduleSpec
from authentik.tasks.schedules.models import Schedule


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

    def test_schedule_delete_keeps_task_logs(self):
        """Test schedule deletion doesn't cascade to task history."""

        @actor
        def test_task():
            pass

        schedule = ScheduleSpec(
            actor=test_task,
            uid="test-schedule-delete-keeps-task-logs",
            crontab="* * * * *",
        ).update_or_create()
        message = Schedule.objects.get(pk=schedule.pk).send()
        task = Task.objects.get(message_id=message.message_id)

        schedule.delete()

        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.assertGreater(TaskLog.objects.filter(task=task).count(), 0)
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
