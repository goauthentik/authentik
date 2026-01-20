import asyncio
import functools
import types
import zlib
from base64 import b64decode
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from re import Pattern
from typing import Any, cast
from uuid import uuid4

import msgpack
from channels.layers import BaseChannelLayer
from django.db import DEFAULT_DB_ALIAS, connections
from django.utils.timezone import now
from psycopg import AsyncConnection, Notify, sql
from psycopg.conninfo import make_conninfo
from psycopg.errors import Error as PsycopgError
from psycopg_pool import AsyncConnectionPool
from structlog.stdlib import get_logger

from django_channels_postgres.models import NOTIFY_CHANNEL, GroupChannel, Message

LOGGER = get_logger()


GROUP_CHANNEL_TABLE = GroupChannel._meta.db_table
MESSAGE_TABLE = Message._meta.db_table


async def _async_proxy(
    obj: PostgresChannelLayerLoopProxy,
    name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    # Must be defined as a function and not a method due to
    # https://bugs.python.org/issue38364
    layer = obj._get_layer()
    return await getattr(layer, name)(*args, **kwargs)


def _wrap_close(proxy: PostgresChannelLayerLoopProxy, loop: asyncio.AbstractEventLoop) -> None:
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
        m = cast(bytes, msgpack.packb(message, use_bin_type=True))
        c = zlib.compress(m, 6)
        return c

    def deserialize(self, message: bytes) -> dict[str, Any]:
        """Deserializes from a byte string."""
        m = zlib.decompress(message)
        return cast(dict[str, Any], msgpack.unpackb(m, raw=False))

    def _get_layer(self) -> PostgresChannelLoopLayer:
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
        self._pool_lock = asyncio.Lock()

        # Each consumer gets its own *specific* channel, created with the `new_channel()` method.
        # This dict maps `channel_name` to a queue of messages for that channel.
        self.channels: dict[str, asyncio.Queue[tuple[str, bytes | None]]] = {}

        self._pool: AsyncConnectionPool | None = None
        self.receiver = PostgresChannelLayerReceiver(self.using, self)

    def make_conninfo(self) -> str:
        db_params = connections[self.using].get_connection_params()
        # Prevent psycopg from using the custom synchronous cursor factory from django
        db_params.pop("cursor_factory")
        db_params.pop("context")
        return make_conninfo(conninfo="", **db_params, connect_timeout=10)

    async def connection(self) -> AbstractAsyncContextManager[AsyncConnection]:
        if self._pool is None:
            async with self._pool_lock:

                async def _configure_connection(conn: AsyncConnection) -> None:
                    await conn.set_autocommit(True)
                    conn.prepare_threshold = 0  # All statements should be prepared
                    conn.prepared_max = None  # No limit on the number of prepared statements

                self._pool = AsyncConnectionPool(
                    conninfo=self.make_conninfo(),
                    open=False,
                    configure=_configure_connection,
                    min_size=1,
                    max_size=4,
                )
                await self._pool.open(wait=True)
        return self._pool.connection()

    async def _subscribe_to_channel(self, channel: str) -> None:
        self.channels[channel] = asyncio.Queue()
        await self.receiver.subscribe(channel)

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

        async with await self.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    sql.SQL("""
                        INSERT INTO {table}
                        ({id}, {channel}, {message}, {expires})
                        VALUES (%s, %s, %s, %s)
                        """).format(
                        table=sql.Identifier(MESSAGE_TABLE),
                        id=sql.Identifier("id"),
                        channel=sql.Identifier("channel"),
                        message=sql.Identifier("message"),
                        expires=sql.Identifier("expires"),
                    ),
                    (
                        uuid4(),
                        channel,
                        self.channel_layer.serialize(message),
                        now() + timedelta(seconds=self.expiry),
                    ),
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
        """
        if channel not in self.channels:
            await self._subscribe_to_channel(channel)

        q = self.channels[channel]
        try:
            while True:
                message_id, message = await q.get()
                if message is None:
                    async with await self.connection() as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute(
                                sql.SQL("""
                                    SELECT {table}.{message}
                                    FROM {table}
                                    WHERE {table}.{id} = %s
                                    """).format(
                                    table=sql.Identifier(MESSAGE_TABLE),
                                    id=sql.Identifier("id"),
                                    message=sql.Identifier("message"),
                                ),
                                (message_id,),
                            )
                            row = await cursor.fetchone()
                            if row is None:
                                continue
                            message = row[0]
                break
        except asyncio.CancelledError, TimeoutError, GeneratorExit:
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
                    await self.receiver.unsubscribe(channel)
                except BaseException as exc:  # noqa: BLE001
                    LOGGER.warning("Unexpected exception while cleaning-up channel", exc=exc)
                    # We don't re-raise here because we want the CancelledError to be the one
                    # re-raised
            raise
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

        async with await self.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    sql.SQL("""
                        INSERT INTO {table}
                        ({id}, {group_key}, {channel}, {expires})
                        VALUES (%s, %s, %s, %s)
                        """).format(
                        table=sql.Identifier(GROUP_CHANNEL_TABLE),
                        id=sql.Identifier("id"),
                        group_key=sql.Identifier("group_key"),
                        channel=sql.Identifier("channel"),
                        expires=sql.Identifier("expires"),
                    ),
                    (
                        uuid4(),
                        group_key,
                        channel,
                        now() + timedelta(seconds=self.group_expiry),
                    ),
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

        async with await self.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    sql.SQL("""
                        DELETE
                        FROM {table}
                        WHERE {table}.{group_key} = %s
                          AND {table}.{channel} = %s
                        """).format(
                        table=sql.Identifier(GROUP_CHANNEL_TABLE),
                        group_key=sql.Identifier("group_key"),
                        channel=sql.Identifier("channel"),
                    ),
                    (group_key, channel),
                )

    async def group_send(self, group: str, message: dict[str, Any]) -> None:
        """
        Sends a message to the entire group.
        """
        assert self.require_valid_group_name(group), "Group name not valid"  # nosec

        group_key = self._group_key(group)

        serialized_message = self.channel_layer.serialize(message)

        async with await self.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    sql.SQL("""
                        SELECT DISTINCT {table}.{channel}
                        FROM {table}
                        WHERE {table}.{group_key} = %s
                        """).format(
                        table=sql.Identifier(GROUP_CHANNEL_TABLE),
                        channel=sql.Identifier("channel"),
                        group_key=sql.Identifier("group_key"),
                    ),
                    (group_key,),
                )
                channels = [row[0] for row in await cursor.fetchall()]
            messages = [
                (uuid4(), channel, serialized_message, now() + timedelta(seconds=self.expiry))
                for channel in channels
            ]
            async with conn.cursor() as cursor:
                await cursor.executemany(
                    sql.SQL("""
                        INSERT INTO {table}
                        ({id}, {channel}, {message}, {expires})
                        VALUES (%s, %s, %s, %s)
                        """).format(
                        table=sql.Identifier(MESSAGE_TABLE),
                        id=sql.Identifier("id"),
                        channel=sql.Identifier("channel"),
                        message=sql.Identifier("message"),
                        expires=sql.Identifier("expires"),
                    ),
                    messages,
                )

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
        await self.receiver.flush()


class PostgresChannelLayerReceiver:
    def __init__(self, using: str, channel_layer: PostgresChannelLoopLayer) -> None:
        self.using = using
        self.channel_layer = channel_layer
        self._subscribed_to: set[str] = set()
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
                async with await AsyncConnection.connect(
                    conninfo=self.channel_layer.make_conninfo(),
                    autocommit=True,
                ) as conn:
                    await self._process_backlog(conn)
                    await conn.execute(
                        sql.SQL("LISTEN {channel}").format(channel=sql.Identifier(NOTIFY_CHANNEL))
                    )
                    while True:
                        async for notify in conn.notifies(timeout=30):
                            await self._receive_notify(notify)
            except asyncio.CancelledError, TimeoutError, GeneratorExit:
                raise
            except PsycopgError as exc:
                LOGGER.warning("Postgres connection is not healthy", exc=exc)
            except BaseException as exc:  # noqa: BLE001
                LOGGER.warning("Unexpected exception in receive task", exc=exc, exc_info=True)
            await asyncio.sleep(1)

    async def _process_backlog(self, conn: AsyncConnection) -> None:
        if not self._subscribed_to:
            return
        async with conn.cursor() as cursor:
            await cursor.execute(
                sql.SQL("""
                    DELETE
                    FROM {table}
                    WHERE {table}.{channel} = ANY(%s)
                      AND {table}.{expires} >= %s
                    RETURNING {table}.{id}, {table}.{channel}, {table}.{message}
                """).format(
                    table=sql.Identifier(MESSAGE_TABLE),
                    id=sql.Identifier("id"),
                    channel=sql.Identifier("channel"),
                    expires=sql.Identifier("expires"),
                    message=sql.Identifier("message"),
                ),
                (list(self._subscribed_to), now()),
            )
            async for row in cursor:
                message_id, channel, message = row
                self._receive_message(channel, message_id, message)

    async def _receive_notify(self, notify: Notify) -> None:
        payload = notify.payload
        split_payload = payload.split(":")
        message: bytes | None = None
        match len(split_payload):
            case 4:
                message_id, channel, timestamp, base64_message = split_payload
                if channel not in self._subscribed_to:
                    return
                expires = datetime.fromtimestamp(float(timestamp), tz=UTC)
                if expires < now():
                    return
                message = b64decode(base64_message)
            case 3:
                message_id, channel, timestamp = split_payload
                if channel not in self._subscribed_to:
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
