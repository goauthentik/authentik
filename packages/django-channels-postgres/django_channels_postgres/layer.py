import asyncio
import functools
import types
from base64 import b64decode
from datetime import UTC, datetime, timedelta
from re import Pattern
from typing import Any, cast
from uuid import uuid4

import msgpack
from channels.layers import BaseChannelLayer
from django.db import DEFAULT_DB_ALIAS, connections
from django.utils.timezone import now
from pglock.core import _cast_lock_id
from psycopg import AsyncConnection, Notify, sql
from psycopg.conninfo import make_conninfo
from psycopg.errors import Error as PsycopgError
from structlog.stdlib import get_logger

from django_channels_postgres.models import NOTIFY_CHANNEL, GroupChannel, Message

LOGGER = get_logger()


GROUP_CHANNEL_TABLE = GroupChannel._meta.db_table
MESSAGE_TABLE = Message._meta.db_table


async def _async_proxy(
    obj: "PostgresChannelLayerLoopProxy",
    name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    # Must be defined as a function and not a method due to
    # https://bugs.python.org/issue38364
    layer = obj._get_layer()
    return await getattr(layer, name)(*args, **kwargs)


def _wrap_close(proxy: "PostgresChannelLayerLoopProxy", loop: asyncio.AbstractEventLoop) -> None:
    original_impl = loop.close

    def _wrapper(self: asyncio.AbstractEventLoop, *args: Any, **kwargs: Any) -> None:
        if loop in proxy._layers:
            layer = proxy._layers[loop]
            del proxy._layers[loop]
            loop.run_until_complete(layer.flush())
        self.close = original_impl  # type: ignore[method-assign]
        return self.close(*args, **kwargs)

    loop.close = types.MethodType(_wrapper, loop)  # type: ignore[method-assign]


class PostgresChannelLayerLoopProxy:
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._args = args
        self._kwargs = kwargs
        self._kwargs["channel_layer"] = self
        self._layers: dict[asyncio.AbstractEventLoop, PostgresChannelLoopLayer] = {}

    def __getattr__(self, name: str) -> Any:
        if name in (
            "new_channel",
            "send",
            "receive",
            "group_add",
            "group_discard",
            "group_send",
            "flush",
        ):
            return functools.partial(_async_proxy, self, name)
        else:
            return getattr(self._get_layer(), name)

    def serialize(self, message: dict[str, Any]) -> bytes:
        """Serializes message to a byte string."""
        return cast(bytes, msgpack.packb(message, use_bin_type=True))

    def deserialize(self, message: bytes) -> dict[str, Any]:
        """Deserializes from a byte string."""
        return cast(dict[str, Any], msgpack.unpackb(message, raw=False))

    def _get_layer(self) -> "PostgresChannelLoopLayer":
        loop = asyncio.get_running_loop()

        try:
            layer = self._layers[loop]
        except KeyError:
            layer = PostgresChannelLoopLayer(*self._args, **self._kwargs)
            self._layers[loop] = layer
            _wrap_close(self, loop)

        return layer


PostgresChannelLayer = PostgresChannelLayerLoopProxy


class PostgresChannelLoopLayer(BaseChannelLayer):
    """
    Postgres channel layer.

    It uses the NOTIFY/LISTEN functionality of postgres to broadcast messages

    It also makes use of an internal message table to overcome the
    8000bytes limit of Postgres' NOTIFY messages.
    Which is a far cry from the channels standard of 1MB
    This table has a trigger that sends out the `NOTIFY` signal.

    Using a database also means messages are durable and will always be
    available to consumers (as long as they're not expired).
    """

    def __init__(
        self,
        channel_layer: PostgresChannelLayerLoopProxy,
        prefix: str = "asgi",
        expiry: int = 60,
        group_expiry: int = 86400,
        capacity: int = 100,
        channel_capacity: dict[Pattern[str] | str, int] | None = None,
        using: str = DEFAULT_DB_ALIAS,
    ) -> None:
        super().__init__(expiry=expiry, capacity=capacity, channel_capacity=channel_capacity)

        self.group_expiry = group_expiry
        self.prefix = prefix
        assert isinstance(self.prefix, str), "Prefix must be unicode"  # nosec
        self.channel_layer = channel_layer
        self.using = using

        # Each consumer gets its own *specific* channel, created with the `new_channel()` method.
        # This dict maps `channel_name` to a queue of messages for that channel.
        self.channels: dict[str, asyncio.Queue[tuple[str, bytes | None]]] = {}

        self.connection = PostgresChannelLayerConnection(self.using, self)

    async def _subscribe_to_channel(self, channel: str) -> None:
        self.channels[channel] = asyncio.Queue()
        await self.connection.subscribe(channel)

    extensions = ["groups", "flush"]

    ### Channel layer API ###

    async def send(self, channel: str, message: dict[str, Any]) -> None:
        """
        Send a message onto a (general or specific) channel.
        """
        # Typecheck
        assert isinstance(message, dict), "message is not a dict"  # nosec
        assert self.require_valid_channel_name(channel), "Channel name not valid"  # nosec
        # Make sure the message does not contain reserved keys
        assert "__asgi_channel__" not in message  # nosec

        await Message.objects.using(self.using).acreate(
            channel=channel,
            message=self.channel_layer.serialize(message),
            expires=now() + timedelta(seconds=self.expiry),
        )

    async def new_channel(self, prefix: str = "specific") -> str:
        """
        Returns a new channel name that can be used by something in our
        process as a specific channel.
        """
        channel = f"{self.prefix}.{prefix}.{uuid4().hex}"
        await self._subscribe_to_channel(channel)
        return channel

    async def receive(self, channel: str) -> dict[str, Any]:
        """
        Receive the first message that arrives on the channel.
        If more than one coroutine waits on the same channel, the first waiter
        will be given the message when it arrives.

        This is done by acquiring an `advistory_lock` from the database
        based on the channel name.

        If the lock is acquired successfully, subsequent calls to this method
        will not try to acquire the lock again.
        _The lock is session based and should be released by postgres when
        the session is closed_

        If the lock is already acquired by another coroutine,
        subsequent calls to this method will repeatedly try to acquire the lock
        before proceeding to wait for a message.
        """
        if channel not in self.channels:
            await self._subscribe_to_channel(channel)

        q = self.channels[channel]
        try:
            while True:
                (message_id, message) = await q.get()
                if message is None:
                    m = await Message.objects.filter(pk=message_id).afirst()
                    if m is None:
                        continue
                    message = cast(bytes, m.message)
                break
        except (asyncio.CancelledError, TimeoutError, GeneratorExit):
            # We assume here that the reason we are cancelled is because the consumer
            # is exiting, therefore we need to cleanup by unsubscribe below. Indeed,
            # currently the way that Django Channels works, this is a safe assumption.
            # In the future, Django Channels could change to call a *new* method that
            # would serve as the antithesis of `new_channel()`; this new method might
            # be named `delete_channel()`. If that were the case, we would do the
            # following cleanup from that new `delete_channel()` method, but, since
            # that's not how Django Channels works (yet), we do the cleanup below:
            if channel in self.channels:
                del self.channels[channel]
                try:
                    await self.connection.unsubscribe(channel)
                except BaseException as exc:  # noqa: BLE001
                    LOGGER.warning("Unexpected exception while cleaning-up channel", exc=exc)
                    # We don't re-raise here because we want the CancelledError to be the one
                    # re-raised
            raise
        await Message.objects.filter(pk=message_id).adelete()
        return self.channel_layer.deserialize(message)

    # ==============================================================
    # Groups extension
    # ==============================================================

    async def group_add(self, group: str, channel: str) -> None:
        """
        Adds the channel name to a group.
        """
        # Check the inputs
        assert self.require_valid_group_name(group), "Group name not valid"  # nosec
        assert self.require_valid_channel_name(channel), "Channel name not valid"  # nosec

        group_key = self._group_key(group)

        await GroupChannel.objects.using(self.using).aupdate_or_create(
            group_key=group_key,
            channel=channel,
            defaults={
                "expires": now() + timedelta(seconds=self.group_expiry),
            },
        )

    async def group_discard(self, group: str, channel: str) -> None:
        """
        Removes the channel from the named group if it is in the group;
        does nothing otherwise (does not error)
        """
        # Check the inputs
        assert self.require_valid_group_name(group), "Group name not valid"  # nosec
        assert self.require_valid_channel_name(channel), "Channel name not valid"  # nosec

        group_key = self._group_key(group)

        await (
            GroupChannel.objects.using(self.using)
            .filter(group_key=group_key, channel=channel)
            .adelete()
        )

    async def group_send(self, group: str, message: dict[str, Any]) -> None:
        """
        Sends a message to the entire group.
        """
        assert self.require_valid_group_name(group), "Group name not valid"  # nosec

        group_key = self._group_key(group)

        serialized_message = self.channel_layer.serialize(message)
        messages = [
            Message(
                channel=channel,
                message=serialized_message,
                expires=now() + timedelta(seconds=self.expiry),
            )
            async for channel in GroupChannel.objects.using(self.using)
            .filter(group_key=group_key, expires__gte=now())
            .values_list("channel", flat=True)
            .distinct()
        ]
        await Message.objects.using(self.using).abulk_create(messages)

    def _group_key(self, group: str) -> str:
        """
        Common function to make the storage key for the group.
        """
        return f"{self.prefix}.group.{group}"

    ### Flush extension ###

    async def flush(self) -> None:
        """
        Deletes all messages and groups.
        """
        self.channels = {}
        await self.connection.flush()


class PostgresChannelLayerConnection:
    def __init__(self, using: str, channel_layer: PostgresChannelLoopLayer) -> None:
        self.using = using
        self.channel_layer = channel_layer
        self._subscribed_to: set[str] = set()
        self._locked_channels: set[str] = set()
        self._lock = asyncio.Lock()
        self._receive_task: asyncio.Task[None] | None = None

    async def subscribe(self, channel: str) -> None:
        async with self._lock:
            if channel not in self._subscribed_to:
                self._ensure_receiver()
                self._subscribed_to.add(channel)

    async def unsubscribe(self, channel: str) -> None:
        async with self._lock:
            if channel in self._subscribed_to:
                self._ensure_receiver()
                self._subscribed_to.remove(channel)

    async def flush(self) -> None:
        async with self._lock:
            if self._receive_task is not None:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
                self._receive_task = None
            self._subscribed_to = set()

    async def _do_receiving(self) -> None:
        while True:
            try:
                async with await self._create_connection() as conn:
                    await self._update_locks(conn)
                    await self._process_backlog(conn)
                    while True:
                        await conn.execute(
                            sql.SQL("LISTEN {channel}").format(
                                channel=sql.Identifier(NOTIFY_CHANNEL)
                            )
                        )
                        async for notify in conn.notifies(timeout=30, stop_after=1):
                            await self._receive_notify(conn, notify)
                        await self._update_locks(conn)
            except (asyncio.CancelledError, TimeoutError, GeneratorExit):
                raise
            except PsycopgError as exc:
                LOGGER.warning("Postgres connection is not healthy", exc=exc)
            except BaseException as exc:  # noqa: BLE001
                LOGGER.warning("Unexpected exception in receive task", exc=exc, exc_info=True)
            self._locked_channels = set()
            await asyncio.sleep(1)

    async def _process_backlog(self, conn: AsyncConnection) -> None:
        if not self._locked_channels:
            return
        async with conn.cursor() as cursor:
            await cursor.execute(
                sql.SQL(
                    """
                    DELETE
                    FROM {table}
                    WHERE
                        {table}.{channel} IN (%s)
                        AND {table}.{expires} >= %s
                    RETURNING {table}.{id}, {table}.{channel}, {table}.{message}
                """
                ).format(
                    table=sql.Identifier(MESSAGE_TABLE),
                    id=sql.Identifier("id"),
                    channel=sql.Identifier("channel"),
                    expires=sql.Identifier("expires"),
                    message=sql.Identifier("message"),
                ),
                (tuple(self._locked_channels), now()),
            )
            async for row in cursor:
                message_id, channel, message = row
                self._receive_message(channel, message_id, message)

    def _get_lock_id(self, channel: str) -> int:
        lock_id = _cast_lock_id(f"channels.{channel}")  # type: ignore[no-untyped-call]
        return cast(int, lock_id)

    async def _update_locks(self, conn: AsyncConnection) -> None:
        async with self._lock:
            locks_to_release = self._locked_channels - self._subscribed_to
            locks_to_acquire = self._subscribed_to - self._locked_channels

            for channel in locks_to_acquire:
                lock_id = self._get_lock_id(channel)
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT pg_try_advisory_lock(%s)", (lock_id,))
                    row = await cursor.fetchone()
                    if row is not None:
                        if row[0]:
                            self._locked_channels.add(channel)

            for channel in locks_to_release:
                lock_id = self._get_lock_id(channel)
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT pg_advisory_unlock(%s)", (lock_id,))
                    row = await cursor.fetchone()
                    if row is not None:
                        if row[0]:
                            self._locked_channels.remove(channel)

    async def _receive_notify(self, conn: AsyncConnection, notify: Notify) -> None:
        payload = notify.payload
        split_payload = payload.split(":")
        message: bytes | None = None
        match len(split_payload):
            case 4:
                message_id, channel, timestamp, base64_message = split_payload
                if channel not in self._locked_channels:
                    return
                expires = datetime.fromtimestamp(float(timestamp), tz=UTC)
                if expires < now():
                    return
                message = b64decode(base64_message)
            case 3:
                message_id, channel, timestamp = split_payload
                if channel not in self._locked_channels:
                    return
                expires = datetime.fromtimestamp(float(timestamp), tz=UTC)
                if expires < now():
                    return
                message = None
            case _:
                return
        self._receive_message(channel, message_id, message)

    def _receive_message(self, channel: str, message_id: str, message: bytes | None) -> None:
        if (q := self.channel_layer.channels.get(channel)) is not None:
            q.put_nowait((message_id, message))

    def _ensure_receiver(self) -> None:
        if self._receive_task is None:
            self._receive_task = asyncio.ensure_future(self._do_receiving())

    async def _create_connection(self) -> AsyncConnection:
        db_params = connections[self.using].get_connection_params()
        # Prevent psycopg from using the custom synchronous cursor factory from django
        db_params.pop("cursor_factory")
        db_params.pop("context")
        conninfo = make_conninfo(conninfo="", **db_params, connect_timeout=10)
        return await AsyncConnection.connect(conninfo=conninfo, autocommit=True)
