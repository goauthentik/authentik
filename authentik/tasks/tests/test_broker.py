from datetime import timedelta
from unittest.mock import ANY, MagicMock, call, patch

from django.test import SimpleTestCase, TestCase
from django.utils.timezone import now
from django_dramatiq_postgres.broker import (
    CONSUMABLE_TASK_STATES,
    PENDING_FETCH_LIMIT,
    PostgresBroker,
)
from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import TaskState
from dramatiq.broker import MessageProxy
from dramatiq.message import Message

from authentik.tasks.models import Task, TaskDependency, TaskLog, TaskStatus
from authentik.tenants.utils import get_current_tenant


class TestPostgresConsumer(SimpleTestCase):

    @staticmethod
    def _consumer():
        consumer = object.__new__(PostgresBroker().consumer_class)
        consumer.logger = MagicMock()
        consumer.broker = MagicMock()
        consumer.in_processing = set()
        consumer.to_unlock = set()
        return consumer

    @staticmethod
    def _message(message_id="00000000-0000-0000-0000-000000000001"):
        return MessageProxy(
            Message(
                queue_name="default",
                actor_name="test.actor",
                args=(),
                kwargs={},
                options={"task": MagicMock()},
                message_id=message_id,
            )
        )

    def test_post_process_marks_terminal_before_unlocking(self):
        consumer = self._consumer()
        message = self._message()
        consumer.in_processing.add(message.message_id)
        update = consumer.query_set.filter.return_value.exclude.return_value.update

        def assert_still_processing(*args, **kwargs):
            self.assertIn(message.message_id, consumer.in_processing)
            self.assertNotIn(message.message_id, consumer.to_unlock)

        update.side_effect = assert_still_processing

        consumer._post_process_message(message, TaskState.DONE)

        consumer.query_set.filter.assert_called_once_with(
            message_id=message.message_id,
            queue_name=message.queue_name,
        )
        consumer.query_set.filter.return_value.exclude.assert_called_once_with(
            state=TaskState.QUEUED,
        )
        self.assertEqual(update.call_args.kwargs["state"], TaskState.DONE)
        self.assertEqual(update.call_args.kwargs["message"], b"")
        self.assertNotIn(message.message_id, consumer.in_processing)
        self.assertIn(message.message_id, consumer.to_unlock)

    def test_post_process_keeps_message_locked_when_update_fails(self):
        consumer = self._consumer()
        message = self._message()
        task = message.options["task"]
        consumer.in_processing.add(message.message_id)
        update = consumer.query_set.filter.return_value.exclude.return_value.update
        update.side_effect = RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            consumer._post_process_message(message, TaskState.DONE)

        self.assertIs(message.options["task"], task)
        self.assertIn(message.message_id, consumer.in_processing)
        self.assertNotIn(message.message_id, consumer.to_unlock)

    def test_requeue_does_not_requeue_terminal_messages(self):
        consumer = self._consumer()
        first_message = self._message("00000000-0000-0000-0000-000000000001")
        second_message = self._message("00000000-0000-0000-0000-000000000002")
        consumer.in_processing.add(first_message.message_id)

        consumer.requeue(message for message in (first_message, second_message))

        consumer.query_set.filter.assert_called_once_with(
            message_id__in=[first_message.message_id, second_message.message_id],
        )
        consumer.query_set.filter.return_value.exclude.assert_called_once_with(
            state__in=(TaskState.DONE, TaskState.REJECTED),
        )
        consumer.query_set.filter.return_value.exclude.return_value.update.assert_called_once_with(
            state=TaskState.QUEUED,
        )
        self.assertEqual(
            consumer.to_unlock,
            {first_message.message_id, second_message.message_id},
        )
        self.assertNotIn(first_message.message_id, consumer.in_processing)

    def test_fetch_pending_messages_filters_consumable_states(self):
        consumer = self._consumer()
        consumer.queue_name = "default"
        consumer.timeout = 30
        query_set = consumer.query_set
        queue_query = query_set.exclude.return_value.filter.return_value
        pending_query = queue_query.filter.return_value
        values_list = pending_query.exclude.return_value.order_by.return_value.values_list
        values_list.return_value.__getitem__.return_value = ["00000000-0000-0000-0000-000000000001"]

        pending = consumer._fetch_pending_messages()

        query_set.exclude.assert_called_once_with(message_id__in=consumer.in_processing)
        query_set.exclude.return_value.filter.assert_called_once_with(
            queue_name=consumer.queue_name,
        )
        queue_query.filter.assert_called_once_with(
            state__in=CONSUMABLE_TASK_STATES,
        )
        values_list.return_value.__getitem__.assert_called_once_with(
            slice(None, PENDING_FETCH_LIMIT)
        )
        self.assertEqual(pending, {"00000000-0000-0000-0000-000000000001"})


class TestPostgresConsumerAutoPurge(TestCase):
    def setUp(self):
        self.broker = PostgresBroker()
        self.task_expiration = timedelta(seconds=Conf().task_expiration)
        self.task_purge_interval = timedelta(seconds=Conf().task_purge_interval)

    def _create_task(self, state: TaskState, mtime_age: timedelta, result_expiry) -> Task:
        task = Task.objects.create(
            tenant=get_current_tenant(),
            queue_name="default",
            actor_name="test.actor",
            state=state,
            mtime=now() - mtime_age,
            result_expiry=result_expiry,
        )
        TaskLog.objects.create(
            task=task,
            event="test",
            log_level=TaskStatus.INFO,
            logger="test",
            timestamp=now(),
            attributes={},
        )
        return task

    def _create_expired_task(self, state: TaskState = TaskState.DONE) -> Task:
        return self._create_task(
            state, self.task_expiration + timedelta(hours=1), now() - timedelta(hours=1)
        )

    def _due_consumer(self):
        consumer = self.broker.consume(queue_name="default")
        consumer.task_purge_last_run = now() - self.task_purge_interval
        return consumer

    def test_auto_purge_deletes_expired_tasks(self):
        old = self.task_expiration + timedelta(hours=1)
        past = now() - timedelta(hours=1)
        expired = [
            self._create_expired_task(TaskState.DONE),
            self._create_expired_task(TaskState.REJECTED),
        ]
        survivors = [
            self._create_task(TaskState.DONE, timedelta(hours=1), past),
            self._create_task(TaskState.DONE, old, now() + timedelta(hours=1)),
            self._create_task(TaskState.QUEUED, old, past),
            self._create_task(TaskState.RUNNING, old, past),
        ]
        for task in expired:
            TaskDependency.objects.create(task=task, dependency=survivors[2])
            TaskDependency.objects.create(task=survivors[3], dependency=task)
        TaskDependency.objects.create(task=survivors[2], dependency=survivors[3])
        consumer = self._due_consumer()
        consumer.logger = MagicMock()

        consumer._auto_purge()

        created = [task.pk for task in expired + survivors]
        self.assertCountEqual(
            Task.objects.filter(pk__in=created).values_list("pk", flat=True),
            [task.pk for task in survivors],
        )
        self.assertCountEqual(
            TaskLog.objects.filter(task_id__in=created).values_list("task_id", flat=True),
            [task.pk for task in survivors],
        )
        self.assertEqual(
            list(
                TaskDependency.objects.filter(task_id__in=created).values_list(
                    "task_id", "dependency_id"
                )
            ),
            [(survivors[2].pk, survivors[3].pk)],
        )
        self.assertEqual(
            consumer.logger.info.call_args_list,
            [
                call("Task purge started", queue="default"),
                call("Task purge finished", queue="default", count=len(expired), duration=ANY),
            ],
        )

    def test_auto_purge_not_due_on_first_poll(self):
        task = self._create_expired_task()
        interval = self.task_purge_interval.total_seconds()

        with patch(
            "django_dramatiq_postgres.broker.random.uniform",
            return_value=interval / 2,
        ) as uniform:
            consumer = self.broker.consume(queue_name="default")
        uniform.assert_called_once_with(0, interval)

        consumer._auto_purge()
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

        consumer.task_purge_last_run = now() - self.task_purge_interval
        consumer._auto_purge()
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
