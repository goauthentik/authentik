"""Test aggregated status of tasks"""

from django.test import TestCase
from django_dramatiq_postgres.models import TaskState
from dramatiq import actor, get_broker
from dramatiq.actor import Actor

from authentik.tasks.middleware import CurrentTask
from authentik.tasks.models import Task, TaskStatus


class TestAggregatedStatus(TestCase):
    """Test that a task's aggregated status reflects the logs it wrote

    The status is set by a trigger on the task table, which aggregates the task's logs
    once it is finished.
    """

    def _run(self, task_actor: Actor, state: str = TaskState.DONE) -> str:
        """Run an actor, move the resulting task to the given state, and return its status"""
        message = task_actor.send()
        del get_broker().actors[task_actor.actor_name]
        # The test broker processes a copy of the message on its own queue, while the task
        # keeps the queue it was enqueued on, so the state updates never match it and the
        # task is left as queued (see authentik/tasks/test.py). Move it along the way the
        # broker would, now that all of its logs have been written.
        Task.objects.filter(message_id=message.message_id).update(state=state)
        return Task.objects.get(message_id=message.message_id).aggregated_status

    def test_error(self):
        """Test that a task logging an error is marked as errored"""

        @actor
        def error_task():
            CurrentTask.get_task().error("something went wrong")

        self.assertEqual(self._run(error_task), TaskStatus.ERROR)

    def test_warning(self):
        """Test that a task logging a warning is marked as warned"""

        @actor
        def warning_task():
            CurrentTask.get_task().warning("something looked odd")

        self.assertEqual(self._run(warning_task), TaskStatus.WARNING)

    def test_most_severe_log_wins(self):
        """Test that the most severe log level of a task determines its status"""

        @actor
        def mixed_task():
            self = CurrentTask.get_task()
            self.info("first")
            self.warning("second")
            self.error("third")
            self.info("fourth")

        self.assertEqual(self._run(mixed_task), TaskStatus.ERROR)

    def test_successful(self):
        """Test that a task which only logs informational messages is not marked as failed"""

        @actor
        def successful_task():
            CurrentTask.get_task().info("all good")

        self.assertEqual(self._run(successful_task), TaskStatus.INFO)

    def test_unfinished_task_keeps_state(self):
        """Test that a task which has not finished is reported with its state"""

        @actor
        def rejected_task():
            CurrentTask.get_task().error("something went wrong")

        self.assertEqual(self._run(rejected_task, state=TaskState.REJECTED), TaskStatus.REJECTED)
