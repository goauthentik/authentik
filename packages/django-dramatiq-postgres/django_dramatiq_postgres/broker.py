import functools
import logging
import time
from collections.abc import Iterable
from queue import Empty, Queue
from typing import Any

import tenacity
from django.core.exceptions import ImproperlyConfigured
from django.db import (
    DEFAULT_DB_ALIAS,
    DatabaseError,
    InterfaceError,
    OperationalError,
    connections,
    transaction,
)
from django.db.backends.postgresql.base import DatabaseWrapper
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from dramatiq.broker import Broker, Consumer, MessageProxy
from dramatiq.common import compute_backoff, current_millis, dq_name, xq_name
from dramatiq.errors import ConnectionError, QueueJoinTimeout
from dramatiq.logging import get_logger
from dramatiq.message import Message
from dramatiq.middleware import (
    Middleware,
)
from pglock.core import _cast_lock_id
from psycopg import Notify, sql
from psycopg.errors import AdminShutdown

from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import CHANNEL_PREFIX, ChannelIdentifier, TaskBase, TaskState

logger = get_logger(__name__)


def channel_name(queue_name: str, identifier: ChannelIdentifier) -> str:
    return f"{CHANNEL_PREFIX}.{queue_name}.{identifier.value}"


def raise_connection_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalError as exc:
            raise ConnectionError(str(exc)) from exc

    return wrapper


class PostgresBroker(Broker):
    def __init__(
        self,
        *args,
        middleware: list[Middleware] | None = None,
        db_alias: str = DEFAULT_DB_ALIAS,
        **kwargs,
    ):
        super().__init__(*args, middleware=[], **kwargs)
        self.logger = get_logger(__name__, type(self))

        self.queues = set()

        self.db_alias = db_alias
        self.middleware = []
        if middleware:
            raise ImproperlyConfigured(
                "Middlewares should be set in django settings, not passed directly to the broker."
            )

    @property
    def connection(self) -> DatabaseWrapper:
        return connections[self.db_alias]

    @property
    def consumer_class(self) -> "type[_PostgresConsumer]":
        return _PostgresConsumer

    @cached_property
    def model(self) -> type[TaskBase]:
        return import_string(Conf().task_model)

    @property
    def query_set(self) -> QuerySet:
        return self.model.objects.using(self.db_alias).defer("message", "result")

    def consume(self, queue_name: str, prefetch: int = 1, timeout: int = 30000) -> Consumer:
        self.declare_queue(queue_name)
        return self.consumer_class(
            broker=self,
            db_alias=self.db_alias,
            queue_name=queue_name,
            prefetch=prefetch,
            timeout=timeout,
        )

    def declare_queue(self, queue_name: str):
        if queue_name not in self.queues:
            self.emit_before("declare_queue", queue_name)
            self.queues.add(queue_name)
            # Nothing to do, all queues are in the same table
            self.emit_after("declare_queue", queue_name)

            delayed_name = dq_name(queue_name)
            self.delay_queues.add(delayed_name)
            self.emit_after("declare_delay_queue", delayed_name)

    def model_defaults(self, message: Message) -> dict[str, Any]:
        return {
            "queue_name": message.queue_name,
            "actor_name": message.actor_name,
            "state": TaskState.QUEUED,
        }

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(
            (
                AdminShutdown,
                InterfaceError,
                DatabaseError,
                ConnectionError,
                OperationalError,
            )
        ),
        reraise=True,
        wait=tenacity.wait_random_exponential(multiplier=1, max=5),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(logger, logging.INFO, exc_info=True),
    )
    def enqueue(self, message: Message, *, delay: int | None = None) -> Message:
        canonical_queue_name = message.queue_name
        queue_name = canonical_queue_name
        if delay:
            queue_name = dq_name(queue_name)
            message_eta = current_millis() + delay
            message = message.copy(
                queue_name=queue_name,
                options={
                    "eta": message_eta,
                },
            )

        self.declare_queue(canonical_queue_name)
        self.logger.debug(f"Enqueueing message {message.message_id} on queue {queue_name}")

        message.options["model_defaults"] = self.model_defaults(message)
        self.emit_before("enqueue", message, delay)

        with transaction.atomic(using=self.db_alias):
            query = {
                "message_id": message.message_id,
            }
            defaults = message.options["model_defaults"]
            del message.options["model_defaults"]
            defaults["message"] = message.encode()
            create_defaults = {
                **query,
                **defaults,
            }

            task, created = self.query_set.update_or_create(
                **query,
                defaults=defaults,
                create_defaults=create_defaults,
            )
            message.options["task"] = task
            message.options["task_created"] = created

            self.emit_after("enqueue", message, delay)
        return message

    def get_declared_queues(self) -> set[str]:
        return self.queues.copy()

    def flush(self, queue_name: str):
        self.query_set.filter(
            queue_name__in=(queue_name, dq_name(queue_name), xq_name(queue_name))
        ).delete()

    def flush_all(self):
        for queue_name in self.queues:
            self.flush(queue_name)

    def join(
        self,
        queue_name: str,
        interval: int = 100,
        *,
        timeout: int | None = None,
    ):
        deadline = timeout and time.monotonic() + timeout / 1000
        while True:
            if deadline and time.monotonic() >= deadline:
                raise QueueJoinTimeout(queue_name)

            if self.query_set.filter(
                queue_name=queue_name,
                state__in=(TaskState.QUEUED, TaskState.CONSUMED),
            ).exists():
                return

            time.sleep(interval / 1000)


class _PostgresConsumer(Consumer):
    def __init__(
        self,
        *args,
        broker: PostgresBroker,
        db_alias: str,
        queue_name: str,
        prefetch: int,
        timeout: int,
        **kwargs,
    ):
        self.logger = get_logger(__name__, type(self))

        self.notifies: list[Notify] = []
        self.broker = broker
        self.db_alias = db_alias
        self.queue_name = queue_name
        self.timeout = timeout // 1000
        self.unlock_queue = Queue()
        self.in_processing = set()
        self.prefetch = prefetch
        self.misses = 0
        self._listen_connection: DatabaseWrapper | None = None
        self.postgres_channel = channel_name(self.queue_name, ChannelIdentifier.ENQUEUE)

        # Override because dramatiq doesn't allow us setting this manually
        self.timeout = Conf().worker["consumer_listen_timeout"]

        self.task_purge_interval = timezone.timedelta(seconds=Conf().task_purge_interval)
        self.task_purge_last_run = timezone.now() - self.task_purge_interval

        self.scheduler = None
        if Conf().schedule_model:
            self.scheduler = import_string(Conf().scheduler_class)()
            self.scheduler.broker = self.broker
            self.scheduler_interval = timezone.timedelta(seconds=Conf().scheduler_interval)
            self.scheduler_last_run = timezone.now() - self.scheduler_interval

    @property
    def connection(self) -> DatabaseWrapper:
        return connections[self.db_alias]

    @property
    def query_set(self) -> QuerySet:
        return self.broker.query_set

    @property
    def listen_connection(self) -> DatabaseWrapper:
        if self._listen_connection is not None and self._listen_connection.is_usable():
            return self._listen_connection
        self._listen_connection = connections.create_connection(self.db_alias)
        # Required for notifications
        # See https://www.psycopg.org/psycopg3/docs/advanced/async.html#asynchronous-notifications
        # Should be set to True by Django by default
        self._listen_connection.set_autocommit(True)
        with self._listen_connection.cursor() as cursor:
            cursor.execute(sql.SQL("LISTEN {}").format(sql.Identifier(self.postgres_channel)))
        return self._listen_connection

    @raise_connection_error
    def ack(self, message: Message):
        task = message.options.pop("task", None)
        self.query_set.filter(
            message_id=message.message_id,
            queue_name=message.queue_name,
            state=TaskState.CONSUMED,
        ).update(
            state=TaskState.DONE,
            message=message.encode(),
        )
        message.options["task"] = task
        self.unlock_queue.put_nowait(message.message_id)
        self.in_processing.remove(message.message_id)

    @raise_connection_error
    def nack(self, message: Message):
        task = message.options.pop("task", None)
        self.query_set.filter(
            message_id=message.message_id,
            queue_name=message.queue_name,
        ).exclude(
            state=TaskState.REJECTED,
        ).update(
            state=TaskState.REJECTED,
            message=message.encode(),
        )
        message.options["task"] = task
        self.unlock_queue.put_nowait(message.message_id)
        self.in_processing.remove(message.message_id)

    @raise_connection_error
    def requeue(self, messages: Iterable[Message]):
        self.query_set.filter(
            message_id__in=[message.message_id for message in messages],
        ).update(
            state=TaskState.QUEUED,
        )
        for message in messages:
            self.unlock_queue.put_nowait(message.message_id)
            self.in_processing.remove(message.message_id)
        self._purge_locks()

    def _fetch_pending_notifies(self) -> list[Notify]:
        self.logger.debug(f"Polling for lost messages in {self.queue_name}")
        notifies = (
            self.query_set.filter(
                state__in=(TaskState.QUEUED, TaskState.CONSUMED),
                queue_name=self.queue_name,
            )
            .exclude(
                message_id__in=self.in_processing,
            )
            .values_list("message_id", flat=True)
        )
        return [Notify(pid=0, channel=self.postgres_channel, payload=item) for item in notifies]

    def _poll_for_notify(self):
        with self.listen_connection.cursor() as cursor:
            notifies = list(cursor.connection.notifies(timeout=self.timeout, stop_after=1))
            self.logger.debug(
                f"Received {len(notifies)} postgres notifies on channel {self.postgres_channel}"
            )
            self.notifies += notifies

    def _get_message_lock_id(self, message_id: str) -> int:
        return _cast_lock_id(
            f"{channel_name(self.queue_name, ChannelIdentifier.LOCK)}.{message_id}"
        )

    def _consume_one(self, message: Message) -> bool:
        if message.message_id in self.in_processing:
            self.logger.debug(f"Message {message.message_id} already consumed by self")
            return False

        result = (
            self.query_set.filter(
                message_id=message.message_id,
                state__in=(TaskState.QUEUED, TaskState.CONSUMED),
            )
            .extra(
                where=["pg_try_advisory_lock(%s)"],
                params=[self._get_message_lock_id(message.message_id)],
            )
            .update(
                state=TaskState.CONSUMED,
                mtime=timezone.now(),
            )
        )
        return result == 1

    @raise_connection_error
    def __next__(self) -> MessageProxy | None:
        # This method is called every second

        # If we don't have a connection yet, fetch missed notifications from the table directly
        if self._listen_connection is None:
            # We might miss a notification between the initial query and the first time we wait for
            # notifications, it doesn't matter because we re-fetch for missed messages later on.
            self.notifies = self._fetch_pending_notifies()
            self.logger.debug(
                f"Found {len(self.notifies)} pending messages in queue {self.queue_name}"
            )

        processing = len(self.in_processing)
        if processing >= self.prefetch:
            # Wait and don't consume the message, other worker will be faster
            self.misses, backoff_ms = compute_backoff(self.misses, max_backoff=1000)
            self.logger.debug(
                f"Too many messages in processing: {processing}. Sleeping {backoff_ms} ms"
            )
            time.sleep(backoff_ms / 1000)
            return None

        if not self.notifies:
            self._poll_for_notify()

        if not self.notifies:
            self.notifies[:] = self._fetch_pending_notifies()

        # If we have some notifies, loop to find one to do
        while self.notifies:
            notify = self.notifies.pop(0)
            task: TaskBase | None = (
                self.query_set.defer(None).defer("result").filter(message_id=notify.payload).first()
            )
            if task is None:
                continue
            message = Message.decode(task.message)
            message.options["task"] = task
            if self._consume_one(message):
                self.in_processing.add(message.message_id)
                return MessageProxy(message)
            else:
                self.logger.debug(f"Message {message.message_id} already consumed. Skipping.")

        # No message to process
        self._purge_locks()
        self._auto_purge()
        self._scheduler()

        return None

    def _purge_locks(self):
        while True:
            try:
                message_id = self.unlock_queue.get(block=False)
            except Empty:
                return
            self.logger.debug(f"Unlocking message {message_id}")
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_unlock(%s)", (self._get_message_lock_id(message_id),)
                )
            self.unlock_queue.task_done()

    def _auto_purge(self):
        if timezone.now() - self.task_purge_last_run < self.task_purge_interval:
            return
        self.logger.debug("Running garbage collector")
        count = self.query_set.filter(
            state__in=(TaskState.DONE, TaskState.REJECTED),
            mtime__lte=timezone.now() - timezone.timedelta(seconds=Conf().task_purge_interval),
            result_expiry__lte=timezone.now(),
        ).delete()
        self.logger.info(f"Purged {count} messages in all queues")

    def _scheduler(self):
        if not self.scheduler:
            return
        if timezone.now() - self.scheduler_last_run < self.scheduler_interval:
            return
        self.scheduler.run()

    @raise_connection_error
    def close(self):
        try:
            self._purge_locks()
        finally:
            try:
                self.connection.close()
            finally:
                if self._listen_connection is not None:
                    conn = self._listen_connection
                    self._listen_connection = None
                    conn.close()
