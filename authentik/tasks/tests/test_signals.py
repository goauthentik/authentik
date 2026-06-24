"""Tests for ``authentik.tasks.signals.monitoring_set_queued_tasks``.

Regression guards: the handler must enumerate ``(queue_name, actor_name)``
from the in-memory dramatiq broker registry, not via a
``SELECT DISTINCT ... FROM authentik_tasks_task`` full-table scan.

Pure unit tests — ``Task.objects`` and ``get_broker`` are mocked so no DB
connection is required.
"""

from unittest import TestCase, mock


class _FakeActor:
    def __init__(self, queue_name: str, actor_name: str):
        self.queue_name = queue_name
        self.actor_name = actor_name


class TestMonitoringSetQueuedTasksDoesNotScan(TestCase):
    """The handler must not full-scan ``authentik_tasks_task``."""

    def _run_handler(self, fake_actors, task_objects_mock):
        """Run the handler with mocked broker, Task.objects, and gauge.
        Returns (broker_mock, task_mock, gauge_mock)."""
        from authentik.tasks import signals

        with (
            mock.patch.object(signals, "get_broker") as mock_get_broker,
            mock.patch.object(signals, "Task") as mock_task,
            mock.patch.object(signals, "GAUGE_TASKS_QUEUED") as mock_gauge,
        ):
            mock_get_broker.return_value.actors = fake_actors
            mock_task.objects = task_objects_mock
            signals.monitoring_set_queued_tasks(sender=self)
            return mock_get_broker, mock_task, mock_gauge

    def test_does_not_call_values_distinct_on_task_objects(self):
        """Direct ``Task.objects.values(...).distinct()`` (the old DB-hot path)
        must never be called."""
        fake_actors = {
            "a": _FakeActor("default", "a"),
            "b": _FakeActor("default", "b"),
        }
        task_objects = mock.MagicMock()
        # Empty result for the remaining filter-based query.
        task_objects.filter.return_value.values.return_value.annotate.return_value = []

        _, mock_task, _ = self._run_handler(fake_actors, task_objects)

        # ``values`` called without going through ``filter`` first means
        # something is enumerating the whole table.
        for call in mock_task.objects.values.call_args_list:
            self.fail(
                f"Task.objects.values{call} was called directly — "
                "this would issue a full-table SELECT DISTINCT."
            )

    def test_gauges_set_for_every_registered_actor(self):
        """Every actor registered with the broker has its gauge initialized
        to 0 so prometheus shows the actor's existence even when no tasks
        are queued for it."""
        fake_actors = {
            "actor_a": _FakeActor("queue_x", "actor_a"),
            "actor_b": _FakeActor("queue_y", "actor_b"),
            "actor_c": _FakeActor("queue_x", "actor_c"),
        }
        task_objects = mock.MagicMock()
        task_objects.filter.return_value.values.return_value.annotate.return_value = []

        _, _, mock_gauge = self._run_handler(fake_actors, task_objects)

        labeled_combos = {(c.args[0], c.args[1]) for c in mock_gauge.labels.call_args_list}
        expected_combos = {(actor.queue_name, actor.actor_name) for actor in fake_actors.values()}
        self.assertEqual(labeled_combos, expected_combos)
        for child_call in mock_gauge.labels.return_value.set.call_args_list:
            self.assertEqual(child_call.args, (0,))

    def test_queued_count_query_uses_filter_state_queued(self):
        """The remaining DB query goes through ``.filter(state=QUEUED)`` so
        it can use the ``(queue_name, state)`` index."""
        from django_dramatiq_postgres.models import TaskState

        fake_actors = {"a": _FakeActor("default", "a")}
        task_objects = mock.MagicMock()
        task_objects.filter.return_value.values.return_value.annotate.return_value = [
            {"queue_name": "default", "actor_name": "a", "count": 5},
        ]

        _, mock_task, mock_gauge = self._run_handler(fake_actors, task_objects)

        mock_task.objects.filter.assert_called_once_with(state=TaskState.QUEUED)
        mock_gauge.labels.return_value.set.assert_any_call(5)
