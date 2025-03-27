import functools
import logging
import time
from collections.abc import Iterable
from queue import Empty, Queue
from random import randint

import tenacity
from django.db import (
    DEFAULT_DB_ALIAS,
    DatabaseError,
    InterfaceError,
    OperationalError,
    close_old_connections,
    connections,
)
from django.db.backends.postgresql.base import DatabaseWrapper
from django.db.models import QuerySet
from django.utils import timezone
from dramatiq.broker import Broker, Consumer, MessageProxy
from dramatiq.common import compute_backoff, current_millis, dq_name, xq_name
from dramatiq.errors import ConnectionError, QueueJoinTimeout
from dramatiq.message import Message
from dramatiq.middleware import Middleware, Prometheus, default_middleware
from dramatiq.results import Results
from pglock.core import _cast_lock_id
from psycopg import Notify, sql
from psycopg.errors import AdminShutdown
from structlog.stdlib import get_logger

from authentik.tasks.models import CHANNEL_PREFIX, ChannelIdentifier, Task, TaskState
from authentik.tasks.results import PostgresBackend
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant
from authentik.tasks.schedules.scheduler import Scheduler

LOGGER = get_logger()


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


class DbConnectionMiddleware(Middleware):
    def _close_old_connections(self, *args, **kwargs):
        close_old_connections()

    before_process_message = _close_old_connections
    after_process_message = _close_old_connections

    def _close_connections(self, *args, **kwargs):
        connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections


class TenantMiddleware(Middleware):
    def before_process_message(self, broker: Broker, message: Message):
        Task.objects.select_related("tenant").get(message_id=message.message_id).tenant.activate()

    def after_process_message(self, *args, **kwargs):
        Tenant.deactivate()


class PostgresBroker(Broker):
    def __init__(self, *args, db_alias: str = DEFAULT_DB_ALIAS, results: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger().bind()

        self.queues = set()
        self.actor_options = {
            "schedule_uid",
        }

        self.db_alias = db_alias
        self.middleware = []
        self.add_middleware(DbConnectionMiddleware())
        self.add_middleware(TenantMiddleware())
        for middleware in default_middleware:
            if middleware == Prometheus:
                pass
            self.add_middleware(middleware())
        if results:
            self.backend = PostgresBackend()
            self.add_middleware(Results(backend=self.backend))

    @property
    def connection(self) -> DatabaseWrapper:
        return connections[self.db_alias]

    @property
    def consumer_class(self) -> "type[_PostgresConsumer]":
        return _PostgresConsumer

    @property
    def query_set(self) -> QuerySet:
        return Task.objects.using(self.db_alias)

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
        wait=tenacity.wait_random_exponential(multiplier=1, max=30),
        stop=tenacity.stop_after_attempt(10),
        before_sleep=tenacity.before_sleep_log(LOGGER, logging.INFO, exc_info=True),
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
        self.emit_before("enqueue", message, delay)
        query = {
            "message_id": message.message_id,
        }
        defaults = {
            "tenant": get_current_tenant(),
            "queue_name": message.queue_name,
            "actor_name": message.actor_name,
            "state": TaskState.QUEUED,
            "message": message.encode(),
            "schedule_uid": message.options.get("schedule_uid", ""),
        }
        create_defaults = {
            **query,
            **defaults,
        }
        self.query_set.update_or_create(
            **query,
            defaults=defaults,
            create_defaults=create_defaults,
        )
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
        broker: Broker,
        db_alias: str,
        queue_name: str,
        prefetch: int,
        timeout: int,
        **kwargs,
    ):
        self.logger = get_logger().bind()

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

        self.scheduler = Scheduler(self.broker)

    @property
    def connection(self) -> DatabaseWrapper:
        return connections[self.db_alias]

    @property
    def query_set(self) -> QuerySet:
        return Task.objects.using(self.db_alias)

    @property
    def listen_connection(self) -> DatabaseWrapper:
        if self._listen_connection is not None and self._listen_connection.connection is not None:
            return self._listen_connection
        self._listen_connection = connections[self.db_alias]
        # Required for notifications
        # See https://www.psycopg.org/psycopg3/docs/advanced/async.html#asynchronous-notifications
        # Should be set to True by Django by default
        self._listen_connection.set_autocommit(True)
        with self._listen_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("LISTEN {}").format(
                    sql.Identifier(channel_name(self.queue_name, ChannelIdentifier.ENQUEUE))
                )
            )
        return self._listen_connection

    @raise_connection_error
    def ack(self, message: Message):
        self.unlock_queue.put_nowait(message)
        self.query_set.filter(
            message_id=message.message_id,
            queue_name=message.queue_name,
            state=TaskState.CONSUMED,
        ).update(
            state=TaskState.DONE,
            message=message.encode(),
        )
        self.in_processing.remove(message.message_id)

    @raise_connection_error
    def nack(self, message: Message):
        self.unlock_queue.put_nowait(message)
        self.query_set.filter(
            message_id=message.message_id,
            queue_name=message.queue_name,
            state__ne=TaskState.REJECTED,
        ).update(
            state=TaskState.REJECTED,
            message=message.encode(),
        )
        self.in_processing.remove(message.message_id)

    @raise_connection_error
    def requeue(self, messages: Iterable[Message]):
        self.query_set.filter(
            message_id__in=[message.message_id for message in messages],
        ).update(
            state=TaskState.QUEUED,
        )
        # We don't care about locks, requeue occurs on worker stop

    def _fetch_pending_notifies(self) -> list[Notify]:
        self.logger.debug(f"Polling for lost messages in {self.queue_name}")
        notifies = self.query_set.filter(
            state__in=(TaskState.QUEUED, TaskState.CONSUMED),
            queue_name=self.queue_name,
        ).values_list("message_id", flat=True)
        channel = channel_name(self.queue_name, ChannelIdentifier.ENQUEUE)
        return [Notify(pid=0, channel=channel, payload=item) for item in notifies]

    def _poll_for_notify(self):
        with self.listen_connection.cursor() as cursor:
            notifies = list(cursor.connection.notifies(timeout=self.timeout))
            self.logger.debug(f"Received {len(notifies)} postgres notifies")
            self.notifies += notifies

    def _get_message_lock_id(self, message: Message) -> int:
        return _cast_lock_id(
            f"{channel_name(self.queue_name, ChannelIdentifier.LOCK)}.{message.message_id}"
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
                params=[self._get_message_lock_id(message)],
            )
            .update(
                state=TaskState.CONSUMED,
                mtime=timezone.now(),
            )
        )
        return result == 1

    @raise_connection_error
    def __next__(self):
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
            # Wait and don't consume the message, other worker will be fast
            self.misses, backoff_ms = compute_backoff(self.misses, max_backoff=1000)
            self.logger.debug(
                f"Too many messages in processing: {processing}. Sleeping {backoff_ms} ms"
            )
            time.sleep(backoff_ms / 1000)
            return None

        if not self.notifies:
            self._poll_for_notify()

        if not self.notifies and not randint(0, 300):  # nosec
            # If there aren't any more notifies, randomly poll for missed/crashed messages.
            # Since this method is called every second, this condition limits polling to
            # on average one SELECT every five minutes of inactivity.
            self.notifies[:] = self._fetch_pending_notifies()

        # If we have some notifies, loop to find one to do
        while self.notifies:
            notify = self.notifies.pop(0)
            task = self.query_set.get(message_id=notify.payload)
            message = Message.decode(task.message)
            if self._consume_one(message):
                self.in_processing.add(message.message_id)
                return MessageProxy(message)
            else:
                self.logger.debug(f"Message {message.message_id} already consumed. Skipping.")

        # No message to process
        self._purge_locks()
        self._auto_purge()
        self._run_scheduler()

    def _purge_locks(self):
        while True:
            try:
                message = self.unlock_queue.get(block=False)
            except Empty:
                return
            self.logger.debug(f"Unlocking {message.message_id}@{message.queue_name}")
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_unlock(%s)", (self._get_message_lock_id(message),)
                )
            self.unlock_queue.task_done()

    def _auto_purge(self):
        # Automatically purge messages on average every 100k iteration.
        # Dramatiq defaults to 1s, so this means one purge every 28 hours.
        if randint(0, 100_000):  # nosec
            return
        self.logger.debug("Running garbage collector")
        count = self.query_set.filter(
            state__in=(TaskState.DONE, TaskState.REJECTED),
            mtime__lte=timezone.now() - timezone.timedelta(days=30),
            result_expiry__lte=timezone.now(),
        ).delete()
        self.logger.info(f"Purged {count} messages in all queues")

    def _run_scheduler(self):
        # Same as above, run on average once every minute
        if randint(0, 60):  # nosec
            return
        self.logger.debug("Running scheduler")
        self.scheduler.run()
