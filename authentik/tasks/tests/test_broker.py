from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django_dramatiq_postgres.broker import CONSUMABLE_TASK_STATES, PostgresBroker
from django_dramatiq_postgres.models import TaskState
from dramatiq.broker import MessageProxy
from dramatiq.message import Message


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
        values_list.return_value = ["00000000-0000-0000-0000-000000000001"]

        pending = consumer._fetch_pending_messages()

        query_set.exclude.assert_called_once_with(message_id__in=consumer.in_processing)
        query_set.exclude.return_value.filter.assert_called_once_with(
            queue_name=consumer.queue_name,
        )
        queue_query.filter.assert_called_once_with(
            state__in=CONSUMABLE_TASK_STATES,
        )
        self.assertEqual(pending, {"00000000-0000-0000-0000-000000000001"})

    def test_reconciles_pending_messages_during_continuous_notifications(self):
        consumer = self._consumer()
        missed_message_id = "00000000-0000-0000-0000-000000000001"
        notified_message_id = "00000000-0000-0000-0000-000000000002"
        missed_message = Message(
            queue_name="default",
            actor_name="test.actor",
            args=(),
            kwargs={},
            options={"task": MagicMock()},
            message_id=missed_message_id,
        )
        consumer.pending = set()
        consumer._listen_connection = MagicMock()
        consumer.prefetch = 1
        consumer.misses = 0
        consumer.timeout = 30
        consumer._next_pending_reconciliation = 5
        consumer._scheduler = MagicMock()
        consumer._purge_locks = MagicMock()
        consumer._auto_purge = MagicMock()
        consumer._backlog_waiting_for_dependencies = MagicMock()
        consumer._poll_for_notify = MagicMock(side_effect=lambda: {notified_message_id})
        consumer._fetch_pending_messages = MagicMock(return_value={missed_message_id})
        consumer._consume_one = MagicMock(
            side_effect=lambda message_id: (
                missed_message if message_id == missed_message_id else None
            )
        )

        with patch(
            "django_dramatiq_postgres.broker.time.monotonic",
            side_effect=(4, 5, 5),
        ):
            self.assertIsNone(next(consumer))
            message = next(consumer)

        self.assertEqual(message.message_id, missed_message_id)
        self.assertEqual(consumer._next_pending_reconciliation, 35)
        consumer._poll_for_notify.assert_called_once_with()
        consumer._fetch_pending_messages.assert_called_once_with()
