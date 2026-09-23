from datetime import timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.test import SimpleTestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils.timezone import now
from django_dramatiq_postgres.broker import CONSUMABLE_TASK_STATES, PostgresBroker
from django_dramatiq_postgres.models import TaskState
from django_tenants.utils import get_public_schema_name
from dramatiq.broker import MessageProxy
from dramatiq.message import Message

from authentik.tasks.models import Task
from authentik.tenants.models import Tenant


class TestPostgresConsumer(SimpleTestCase):
    @staticmethod
    def _consumer():
        consumer = object.__new__(PostgresBroker().consumer_class)
        consumer.logger = MagicMock()
        consumer.broker = MagicMock()
        consumer.in_processing = set()
        consumer.to_unlock = set()
        return consumer

    def _consumer_with_cursor(self, lock_row: tuple[bool] | None, rowcount: int = 0):
        consumer = self._consumer()
        consumer.queue_name = "default"
        consumer.timeout = 30
        consumer.broker.query_set.model._meta.db_table = "authentik_tasks_task"
        cursor = MagicMock()
        cursor.fetchone.return_value = lock_row
        cursor.rowcount = rowcount
        consumer._locks_connection = MagicMock()
        consumer._locks_connection.is_usable.return_value = True
        consumer._locks_connection.cursor.return_value.__enter__.return_value = cursor
        return consumer, cursor

    @staticmethod
    def _executed_sql(cursor) -> list[str]:
        return [str(call.args[0]) for call in cursor.execute.call_args_list]

    def test_consume_one_does_not_lock_when_message_not_consumable(self):
        consumer, cursor = self._consumer_with_cursor(lock_row=None)
        message_id = "00000000-0000-0000-0000-000000000001"

        self.assertIsNone(consumer._consume_one(message_id))

        executed = self._executed_sql(cursor)
        self.assertEqual(len(executed), 1)
        self.assertIn("pg_try_advisory_lock", executed[0])
        self.assertIn("consumable_states", executed[0])
        self.assertIn("maximum_eta", executed[0])
        params = cursor.execute.call_args.args[1]
        self.assertEqual(params["message_id"], message_id)
        self.assertEqual(params["lock_id"], consumer._get_message_lock_id(message_id))
        consumer.broker.query_set.defer.assert_not_called()
        self.assertEqual(consumer.to_unlock, set())
        self.assertNotIn(message_id, consumer.in_processing)

    def test_consume_one_does_not_unlock_when_lock_not_acquired(self):
        consumer, cursor = self._consumer_with_cursor(lock_row=(False,))
        message_id = "00000000-0000-0000-0000-000000000001"

        self.assertIsNone(consumer._consume_one(message_id))

        executed = self._executed_sql(cursor)
        self.assertEqual(len(executed), 1)
        self.assertIn("pg_try_advisory_lock", executed[0])
        consumer.broker.query_set.defer.assert_not_called()
        self.assertEqual(consumer.to_unlock, set())
        self.assertNotIn(message_id, consumer.in_processing)

    def test_consume_one_unlocks_owned_lock_when_update_misses(self):
        consumer, cursor = self._consumer_with_cursor(lock_row=(True,), rowcount=0)
        message_id = "00000000-0000-0000-0000-000000000001"

        self.assertIsNone(consumer._consume_one(message_id))

        executed = self._executed_sql(cursor)
        self.assertEqual(len(executed), 3)
        self.assertIn("pg_try_advisory_lock", executed[0])
        self.assertIn("UPDATE", executed[1])
        self.assertNotIn("pg_try_advisory_lock", executed[1])
        cursor.execute.assert_called_with(
            "SELECT pg_advisory_unlock(%s)",
            (consumer._get_message_lock_id(message_id),),
        )
        consumer.broker.query_set.defer.assert_not_called()
        self.assertNotIn(message_id, consumer.in_processing)

    def test_consume_one_keeps_lock_when_message_consumed(self):
        consumer, cursor = self._consumer_with_cursor(lock_row=(True,), rowcount=1)
        message = Message(
            queue_name="default",
            actor_name="test.actor",
            args=(),
            kwargs={},
            options={},
            message_id="00000000-0000-0000-0000-000000000001",
        )
        task = MagicMock()
        task.message = message.encode()
        query = consumer.broker.query_set.defer.return_value.defer.return_value
        query.filter.return_value.first.return_value = task

        consumed = consumer._consume_one(message.message_id)

        self.assertIsNotNone(consumed)
        self.assertEqual(consumed.message_id, message.message_id)
        self.assertIs(consumed.options["task"], task)
        self.assertIn(message.message_id, consumer.in_processing)
        executed = self._executed_sql(cursor)
        self.assertEqual(len(executed), 2)
        self.assertFalse(any("pg_advisory_unlock" in query for query in executed))

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


class TestPostgresConsumerAdvisoryLocks(TransactionTestCase):
    """Consumers racing for the same message, with real advisory locks.

    Uses committed rows, since each consumer's locks connection is a separate database session.
    """

    UNOWNED_LOCK_WARNING = "you don't own a lock of type ExclusiveLock"

    def setUp(self):
        self.broker = PostgresBroker()
        self.winner = self.broker.consume(queue_name="default")
        self.loser = self.broker.consume(queue_name="default")
        self.message_id = str(uuid4())

    def tearDown(self):
        for consumer in (self.winner, self.loser):
            if consumer._locks_connection is not None:
                consumer._locks_connection.close()

    def _create_task(self, **kwargs) -> Task:
        message = Message(
            queue_name="default",
            actor_name="test.actor",
            args=(),
            kwargs={},
            options={},
            message_id=self.message_id,
        )
        return Task.objects.create(
            message_id=self.message_id,
            queue_name="default",
            actor_name="test.actor",
            message=message.encode(),
            tenant=Tenant.objects.get(schema_name=get_public_schema_name()),
            **kwargs,
        )

    @staticmethod
    def _capture_notices(consumer) -> list[str]:
        notices = []
        connection = consumer.locks_connection
        connection.ensure_connection()
        connection.connection.add_notice_handler(lambda diag: notices.append(diag.message_primary))
        return notices

    @staticmethod
    def _held_advisory_locks(consumer) -> int:
        with consumer.locks_connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM pg_locks "
                "WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted"
            )
            return cursor.fetchone()[0]

    def test_unowned_unlock_warns(self):
        """Unlocking a lock that isn't held logs the warning we want to avoid"""
        notices = self._capture_notices(self.loser)

        self.loser._unlock_message(self.message_id)

        self.assertIn(self.UNOWNED_LOCK_WARNING, notices)

    def test_losing_consumer_does_not_unlock(self):
        self._create_task(state=TaskState.QUEUED)
        winner_notices = self._capture_notices(self.winner)
        loser_notices = self._capture_notices(self.loser)

        consumed = self.winner._consume_one(self.message_id)
        self.assertIsNotNone(consumed)
        self.assertEqual(consumed.message_id, self.message_id)

        with patch.object(
            self.loser, "_unlock_message", wraps=self.loser._unlock_message
        ) as unlock:
            self.assertIsNone(self.loser._consume_one(self.message_id))
            unlock.assert_not_called()

        self.assertEqual(winner_notices, [])
        self.assertEqual(loser_notices, [])
        self.assertEqual(self._held_advisory_locks(self.winner), 1)
        self.assertEqual(self._held_advisory_locks(self.loser), 0)
        self.assertEqual(Task.objects.get(message_id=self.message_id).state, TaskState.CONSUMED)

    def test_not_consumable_message_takes_no_lock(self):
        """Missing, finished or not yet due messages are skipped without taking the lock"""
        cases = {
            "missing": None,
            "done": {"state": TaskState.DONE},
            "rejected": {"state": TaskState.REJECTED},
            "not due": {"state": TaskState.QUEUED, "eta": now() + timedelta(hours=1)},
        }
        for name, task_kwargs in cases.items():
            with self.subTest(name):
                self.message_id = str(uuid4())
                if task_kwargs is not None:
                    self._create_task(**task_kwargs)
                notices = self._capture_notices(self.loser)

                with (
                    patch.object(
                        self.loser, "_unlock_message", wraps=self.loser._unlock_message
                    ) as unlock,
                    CaptureQueriesContext(self.loser.locks_connection) as queries,
                ):
                    self.assertIsNone(self.loser._consume_one(self.message_id))

                unlock.assert_not_called()
                self.assertEqual(len(queries), 1)
                self.assertEqual(notices, [])
                self.assertEqual(self._held_advisory_locks(self.loser), 0)
