from unittest.mock import MagicMock

from django.test import SimpleTestCase
from django_dramatiq_postgres.broker import PostgresBroker
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
