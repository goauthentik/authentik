import functools
import logging
import time
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from typing import Any, ParamSpec, TypeVar, cast

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
from django.db.models.expressions import F
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from dramatiq.broker import Broker, Consumer, MessageProxy
from dramatiq.common import compute_backoff, current_millis, dq_name, q_name, xq_name
from dramatiq.errors import ConnectionError, QueueJoinTimeout
from dramatiq.message import Message
from dramatiq.middleware import (
    Middleware,
)
from pglock.core import _cast_lock_id
from psycopg import sql
from psycopg.errors import AdminShutdown
from structlog.stdlib import get_logger

from django_dramatiq_postgres.conf import Conf
from django_dramatiq_postgres.models import CHANNEL_PREFIX, ChannelIdentifier, TaskBase, TaskState

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


DATABASE_ERRORS = (
    AdminShutdown,
    InterfaceError,
    DatabaseError,
    ConnectionError,
    OperationalError,
)


def channel_name(queue_name: str, identifier: ChannelIdentifier) -> str:
    return f"{CHANNEL_PREFIX}.{queue_name}.{identifier.value}"


def raise_connection_error(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except DATABASE_ERRORS as exc:
            logger.warning("Database error encountered", exc=exc)
            raise ConnectionError(str(exc)) from exc  # type: ignore[no-untyped-call]

    return wrapper


class PostgresBroker(Broker):
    queues: set[str]  # type: ignore[assignment]

    def __init__(
        self,
        *args: Any,
        middleware: list[Middleware] | None = None,
        db_alias: str = DEFAULT_DB_ALIAS,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, middleware=[], **kwargs)  # type: ignore[no-untyped-call,misc]
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
        return cast(DatabaseWrapper, connections[self.db_alias])

    @property
    def consumer_class(self) -> "type[_PostgresConsumer]":
        return _PostgresConsumer

    @cached_property
    def model(self) -> type[TaskBase]:
        model: type[TaskBase] = import_string(Conf().task_model)
        return model

    @property
    def query_set(self) -> QuerySet[TaskBase]:
        return self.model._default_manager.using(self.db_alias).defer("message", "result")

    def consume(self, queue_name: str, prefetch: int = 1, timeout: int = 30000) -> Consumer:
        self.declare_queue(queue_name)
        return self.consumer_class(
            broker=self,
            db_alias=self.db_alias,
            queue_name=queue_name,
            prefetch=prefetch,
            timeout=timeout,
        )

    def declare_queue(self, queue_name: str) -> None:
        if queue_name not in self.queues:
            self.emit_before("declare_queue", queue_name)  # type: ignore[no-untyped-call]
            self.queues.add(queue_name)
            # Nothing more to do, all queues are in the same table
            self.emit_after("declare_queue", queue_name)  # type: ignore[no-untyped-call]

    def model_defaults(self, message: Message[Any]) -> dict[str, Any]:
        eta = None
        if "eta" in message.options:
            eta = datetime.fromtimestamp(message.options["eta"] / 1000, tz=UTC)
            del message.options["eta"]
        return {
            "queue_name": message.queue_name,
            "actor_name": message.actor_name,
            "state": TaskState.QUEUED,
            "retries": message.options.get("retries", 0),
            "eta": eta,
        }

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(ConnectionError),
        reraise=True,
        wait=tenacity.wait_random_exponential(multiplier=1, max=5),
        stop=tenacity.stop_after_attempt(3),
        before_sleep=tenacity.before_sleep_log(
            cast(logging.Logger, logger), logging.INFO, exc_info=True
        ),
    )
    @raise_connection_error
    def enqueue(self, message: Message[Any], *, delay: int | None = None) -> Message[Any]:
        queue_name = q_name(message.queue_name)  # type: ignore[no-untyped-call]
        if delay:
            message_eta = current_millis() + delay  # type: ignore[no-untyped-call]
            message.options["eta"] = message_eta

        self.declare_queue(queue_name)
        self.logger.debug(
            "Enqueueing message on queue", message_id=message.message_id, queue=queue_name
        )

        message.options["model_defaults"] = self.model_defaults(message)
        message.options["model_create_defaults"] = {}
        self.emit_before("enqueue", message, delay)  # type: ignore[no-untyped-call]

        with transaction.atomic(using=self.db_alias):
            query = {
                "message_id": message.message_id,
            }
            defaults = message.options.pop("model_defaults")
            defaults["message"] = message.encode()
            create_defaults = {
                **query,
                **defaults,
                **message.options.pop("model_create_defaults"),
            }

            task, created = self.query_set.update_or_create(
                **query,
                defaults=defaults,
                create_defaults=create_defaults,
            )
            message.options["task"] = task
            message.options["task_created"] = created

            self.emit_after("enqueue", message, delay)  # type: ignore[no-untyped-call]
        return message

    def get_declared_queues(self) -> set[str]:
        return self.queues.copy()

    def flush(self, queue_name: str) -> None:
        self.query_set.filter(
            queue_name__in=(queue_name, dq_name(queue_name), xq_name(queue_name))  # type: ignore[no-untyped-call]
        ).delete()

    def flush_all(self) -> None:
        for queue_name in self.queues:
            self.flush(queue_name)

    def join(
        self,
        queue_name: str,
        interval: int = 100,
        *,
        timeout: int | None = None,
    ) -> None:
        deadline = timeout and time.monotonic() + timeout / 1000
        while True:
            if deadline and time.monotonic() >= deadline:
                raise QueueJoinTimeout(queue_name)  # type: ignore[no-untyped-call]

            if (
                not self.query_set.filter(queue_name=queue_name)
                .exclude(state__in=(TaskState.DONE, TaskState.REJECTED))
                .exists()
            ):
                return

            time.sleep(interval / 1000)


class _PostgresConsumer(Consumer):
    def __init__(
        self,
        *args: Any,
        broker: PostgresBroker,
        db_alias: str,
        queue_name: str,
        prefetch: int,
        timeout: int,
        **kwargs: Any,
    ) -> None:
        self.logger = get_logger(__name__, type(self))

        self.pending: set[str] = set()
        self.broker = broker
        self.db_alias = db_alias
        self.queue_name = queue_name
        self.timeout = timeout // 1000
        self.to_unlock: set[str] = set()
        self.in_processing: set[str] = set()
        self.prefetch = prefetch
        self.misses = 0
        # We have two different connections here. One for locks and one for listening to
        # notifications. We can't use the same connection for both as the listen connection might
        # be blocked with pending notifications. We also can't use a Django connection as we can't
        # be sure we'll get the same one every time to be able to release locks from the same
        # connection.
        self._locks_connection: DatabaseWrapper | None = None
        self._listen_connection: DatabaseWrapper | None = None
        self.postgres_channel = channel_name(self.queue_name, ChannelIdentifier.ENQUEUE)

        # Override because dramatiq doesn't allow us setting this manually
        self.timeout = Conf().worker["consumer_listen_timeout"]

        self.task_purge_interval = timedelta(seconds=Conf().task_purge_interval)
        self.task_purge_last_run = timezone.now() - self.task_purge_interval

        self.scheduler = None
        if Conf().schedule_model:
            self.scheduler = import_string(Conf().scheduler_class)()
            self.scheduler.broker = self.broker
            self.scheduler_interval = timedelta(seconds=Conf().scheduler_interval)
            self.scheduler_last_run = timezone.now() - self.scheduler_interval

    @property
    def query_set(self) -> QuerySet[TaskBase]:
        return self.broker.query_set

    @property
    def locks_connection(self) -> DatabaseWrapper:
        if self._locks_connection is not None and self._locks_connection.is_usable():
            return self._locks_connection
        self._locks_connection = cast(DatabaseWrapper, connections.create_connection(self.db_alias))
        return self._locks_connection

    @property
    def listen_connection(self) -> DatabaseWrapper:
        if self._listen_connection is not None and self._listen_connection.is_usable():
            return self._listen_connection
        self._listen_connection = cast(
            DatabaseWrapper, connections.create_connection(self.db_alias)
        )
        # Required for notifications
        # See https://www.psycopg.org/psycopg3/docs/advanced/async.html#asynchronous-notifications
        # Should be set to True by Django by default
        self._listen_connection.set_autocommit(True)
        with self._listen_connection.cursor() as cursor:
            cursor.execute(sql.SQL("LISTEN {}").format(sql.Identifier(self.postgres_channel)))
        return self._listen_connection

    def _get_message_lock_id(self, message_id: str) -> int:
        lock_id = _cast_lock_id(
            f"{channel_name(self.queue_name, ChannelIdentifier.LOCK)}.{message_id}"
        )  # type: ignore[no-untyped-call]
        return cast(int, lock_id)

    def _fetch_pending_messages(self) -> set[str]:
        self.logger.debug("Fetching for pending messages", queue=self.queue_name)
        pending = set(
            self.query_set.exclude(message_id__in=self.in_processing)
            .filter(queue_name=self.queue_name)
            .exclude(state__in=(TaskState.DONE, TaskState.REJECTED))
            .exclude(eta__gte=timezone.now() + timedelta(seconds=self.timeout))
            .order_by(F("eta").asc(nulls_first=True))
            .values_list("message_id", flat=True)
        )
        self.logger.debug(
            "Finished fetching pending messages in queue",
            pending=len(pending),
            queue=self.queue_name,
        )
        return {str(message_id) for message_id in pending}

    def _poll_for_notify(self) -> set[str]:
        self.logger.debug("Polling for message notifications", queue=self.queue_name)
        with self.listen_connection.cursor() as cursor:
            notifies = list(cursor.connection.notifies(timeout=self.timeout, stop_after=1))
            self.logger.debug(
                "Finished receiving postgres notifies on channel",
                notifies=len(notifies),
                channel=self.postgres_channel,
            )
            return {str(notify.payload) for notify in notifies}

    def _consume_one(self, message_id: str) -> Message[Any] | None:
        if message_id in self.in_processing:
            self.logger.debug("Message already consumed by self", message_id=message_id)
            return None

        with self.locks_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    """
                    UPDATE {table}
                    SET {state} = %(state)s, {mtime} = %(mtime)s
                    WHERE
                        {table}.{message_id} = %(message_id)s
                        AND
                        {table}.{state} != ALL(%(excluded_states)s)
                        AND
                        ({table}.{eta} < %(maximum_eta)s OR {table}.{eta} IS NULL)
                        AND
                        pg_try_advisory_lock(%(lock_id)s)
                    """
                ).format(
                    table=sql.Identifier(self.query_set.model._meta.db_table),
                    state=sql.Identifier("state"),
                    mtime=sql.Identifier("mtime"),
                    message_id=sql.Identifier("message_id"),
                    eta=sql.Identifier("eta"),
                ),
                {
                    "state": TaskState.CONSUMED.value,
                    "mtime": timezone.now(),
                    "message_id": message_id,
                    "excluded_states": [TaskState.DONE.value, TaskState.REJECTED.value],
                    "maximum_eta": timezone.now() + timedelta(seconds=self.timeout),
                    "lock_id": self._get_message_lock_id(message_id),
                },
            )
            if cursor.rowcount != 1:
                self._unlock_message(message_id)
                return None

        task: TaskBase | None = (
            self.query_set.defer(None).defer("result").filter(message_id=message_id).first()
        )
        if task is None:
            return None
        message = Message.decode(cast(bytes, task.message))
        message.options["task"] = task
        self.in_processing.add(str(message_id))
        return message

    @raise_connection_error
    def __next__(self) -> MessageProxy | None:
        # This method is called every second

        # Run required processes first
        self._scheduler()
        self._purge_locks()

        # If we don't have a connection yet, fetch missed notifications from the table directly
        if self._listen_connection is None and not self.pending:
            # We might miss a notification between the initial query and the first time we wait for
            # notifications, it doesn't matter because we re-fetch for missed messages later on.
            self.pending = self._fetch_pending_messages()
            # Force creation of listen connection
            _ = self.listen_connection

        processing = len(self.in_processing)
        if processing >= self.prefetch:
            # If we have too many messages already processing, wait and don't consume a message
            # straight away, other workers will be faster.
            self.misses, backoff_ms = compute_backoff(self.misses, max_backoff=1000)  # type: ignore[no-untyped-call]
            self.logger.debug(
                "Too many messages in processing, Sleeping",
                processing=processing,
                backoff_ms=backoff_ms,
            )
            time.sleep(backoff_ms / 1000)
            return None
        else:
            self.misses = 0

        if not self.pending:
            self.pending = self._poll_for_notify()

        if not self.pending:
            self.pending = self._fetch_pending_messages()

        # If we have some messages pending, loop to find one to process
        while True:
            try:
                message_id = self.pending.pop()
            except KeyError:
                break
            message = self._consume_one(str(message_id))
            if message is not None:
                return MessageProxy(message)  # type: ignore[no-untyped-call]
            else:
                self.logger.debug("Message already consumed. Skipping.", message_id=message_id)
                continue

        # No message to process, we can do some cleaning
        self._auto_purge()

        self.misses = 0
        return None

    def _unlock_message(self, message_id: str) -> bool:
        self.logger.debug("Unlocking message", message_id=message_id)
        try:
            with self.locks_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_unlock(%s)",
                    (self._get_message_lock_id(message_id),),
                )
            return True
        except DATABASE_ERRORS:
            self.to_unlock.add(str(message_id))
            return False

    def _post_process_message(self, message: Message[Any], state: TaskState) -> None:
        self.logger.debug("Post-processing message", message=message.message_id, state=state)
        try:
            self.in_processing.remove(str(message.message_id))
        except KeyError:
            pass
        self.to_unlock.add(str(message.message_id))
        task = message.options.pop("task", None)
        self.query_set.filter(
            message_id=message.message_id,
            queue_name=message.queue_name,
        ).exclude(
            state=TaskState.QUEUED,
        ).update(
            state=state,
            message=message.encode(),
            mtime=timezone.now(),
            eta=None,
        )
        message.options["task"] = task

    @raise_connection_error
    def ack(self, message: Message[Any]) -> None:
        self._post_process_message(message, TaskState.DONE)

    @raise_connection_error
    def nack(self, message: Message[Any]) -> None:
        self._post_process_message(message, TaskState.REJECTED)

    @raise_connection_error
    def requeue(self, messages: Iterable[Message[Any]]) -> None:
        self.query_set.filter(
            message_id__in=[message.message_id for message in messages],
        ).update(
            state=TaskState.QUEUED,
        )
        for message in messages:
            self.to_unlock.add(str(message.message_id))
            self.in_processing.remove(str(message.message_id))

    def _scheduler(self) -> None:
        if not self.scheduler:
            return
        if timezone.now() - self.scheduler_last_run < self.scheduler_interval:
            return
        self.scheduler.run()
        self.schedule_last_run = timezone.now()

    def _purge_locks(self) -> None:
        while True:
            try:
                message_id = self.to_unlock.pop()
            except KeyError:
                break
            if not self._unlock_message(str(message_id)):
                return

    def _auto_purge(self) -> None:
        if timezone.now() - self.task_purge_last_run < self.task_purge_interval:
            return
        self.logger.debug("Running garbage collector")
        count = self.query_set.filter(
            state__in=(TaskState.DONE, TaskState.REJECTED),
            mtime__lte=timezone.now() - timedelta(seconds=Conf().task_expiration),
            result_expiry__lte=timezone.now(),
        ).delete()
        self.logger.info("Purged messages in all queues", count=count)
        self.task_purge_last_run = timezone.now()

    @raise_connection_error
    def close(self) -> None:
        try:
            self._purge_locks()
        finally:
            if self._locks_connection is not None:
                conn = self._locks_connection
                self._locks_connection = None
                try:
                    conn.close()
                except DATABASE_ERRORS:
                    pass
            if self._listen_connection is not None:
                conn = self._listen_connection
                self._listen_connection = None
                try:
                    conn.close()
                except DATABASE_ERRORS:
                    pass
            try:
                connections.close_all()
            except DATABASE_ERRORS:
                pass
