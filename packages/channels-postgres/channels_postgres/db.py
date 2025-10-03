"""common db methods."""

import asyncio
import hashlib
import random
import typing
from datetime import timedelta

import psycopg_pool
import psycopg_pool.base
from django.db import DEFAULT_DB_ALIAS
from django.utils.timezone import now
from psycopg import sql
from structlog.stdlib import get_logger

from .models import GroupChannel, Message

try:
    from datetime import UTC
except ImportError:
    UTC = None  # type: ignore


if typing.TYPE_CHECKING:
    pass


# Enable pool logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
# logging.getLogger('psycopg.pool').setLevel(logging.DEBUG)


# A global variable is used to ensure only one connection pool is created
# regardless of the amount of threads
# And also to prevent RuntimeErrors when the event loop is closed after running tests
# and psycopg Async workers are not cleaned up properly
is_creating_connection_pool = asyncio.Lock()
connection_pool: psycopg_pool.AsyncConnectionPool | None = None

MESSAGE_TABLE = Message._meta.db_table
GROUP_CHANNEL_TABLE = GroupChannel._meta.db_table


class DatabaseLayer:
    """
    Encapsulates database operations

    A connection pool is used for efficient management of database operations
    This is also the reason why psycopg is used directly instead of django's ORM
    which doesn't support connection pooling
    """

    def __init__(
        self,
        using: str = DEFAULT_DB_ALIAS,
    ) -> None:
        self.logger = get_logger(__name__, type(self))
        self.using = using

    async def send_to_channel(
        self,
        group_key: str,
        message: bytes,
        expire: int,
        channel: str | None = None,
    ) -> None:
        """Send a message to a channel/channels (if no channel is specified)."""
        if channel is None:
            channels = (
                GroupChannel.objects.filter(group_key=group_key)
                .values_list("channel", flat=True)
                .distinct()
            )
            if not await channels.aexists():
                self.logger.warning("Group: %s does not exist, did you call group_add?", group_key)
                return
            channels = [channel async for channel in channels]
        else:
            channels = [channel]

        messages = [
            Message(
                channel=channel,
                message=message,
                expire=now() + timedelta(seconds=expire),
            )
            for channel in channels
        ]
        await Message.objects.abulk_create(messages)

    async def add_channel_to_group(self, group_key: str, channel: str, expire: int) -> None:
        """Adds a channel to a group"""
        await GroupChannel.objects.acreate(
            group_key=group_key,
            channel=channel,
            expire=now() + timedelta(seconds=expire),
        )
        self.logger.debug("Channel %s added to Group %s", channel, group_key)

    async def delete_expired_groups(self) -> None:
        """Deletes expired groups after a random delay"""
        expire = 60 * random.randint(10, 20)
        self.logger.debug("Deleting expired groups in %s seconds...", expire)
        await asyncio.sleep(expire)

        await GroupChannel.objects.filter(expire__lt=now()).adelete()

    async def delete_expired_messages(self, expire: int | None = None) -> None:
        """Deletes expired messages after a set time or random delay"""
        if expire is None:
            expire = 60 * random.randint(10, 20)
        self.logger.debug("Deleting expired messages in %s seconds...", expire)
        await asyncio.sleep(expire)

        await Message.objects.filter(expire__lt=now()).adelete()

    async def retrieve_non_expired_queued_messages(self) -> list[tuple[str, str, bytes, str]]:
        """
        Retrieves all non-expired messages from the database

        NOTE: Postgres doesn't support ORDER BY for `RETURNING`
        queries. Even if the inner query is ordered, the returning
        clause is not guaranteed to be ordered
        """
        retrieve_queued_messages_sql = sql.SQL(
            """
            DELETE FROM {table}
            WHERE id IN (
                SELECT id
                FROM {table}
                WHERE expire > %s
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id::text, channel, message, extract(epoch from expire)::text
        """
        ).format(table=sql.Identifier(MESSAGE_TABLE))

        db_pool = await self.get_db_pool(db_params=self.db_params)
        async with db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(retrieve_queued_messages_sql, (now(),))

                return await cursor.fetchall()

    async def retrieve_non_expired_queued_message_from_channel(
        self, channel: str
    ) -> tuple[bytes] | None:
        """Retrieves a non-expired message from a channel"""
        retrieve_queued_messages_sql = sql.SQL(
            """
            DELETE FROM {table}
            WHERE id = (
                SELECT id
                FROM {table}
                WHERE channel=%s AND expire > %s
                ORDER BY id
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                )
            RETURNING message
        """
        ).format(table=sql.Identifier(MESSAGE_TABLE))

        db_pool = await self.get_db_pool(db_params=self.db_params)
        async with db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(retrieve_queued_messages_sql, (channel, now()))
                message = await cursor.fetchone()

                return typing.cast(tuple[bytes] | None, message)

    def _channel_to_constant_bigint(self, channel: str) -> int:
        """
        Converts a channel name to a constant bigint.
        """
        # Hash the character (SHA-256 gives consistent output)
        hash_bytes = hashlib.sha256(channel.encode("utf-8")).digest()
        # Convert to a large int
        hash_int = int.from_bytes(hash_bytes, byteorder="big")

        # Fit into signed 64-bit bigint range
        signed_bigint = hash_int % (2**64)
        if signed_bigint >= 2**63:
            signed_bigint -= 2**64  # Convert to negative if above max signed

        return signed_bigint

    async def acquire_advisory_lock(self, channel: str) -> bool:
        """Acquires an advisory lock from the database"""
        advisory_lock_id = self._channel_to_constant_bigint(channel)
        acquire_advisory_lock_sql = sql.SQL("SELECT pg_try_advisory_lock(%s::bigint)").format(
            advisory_lock_id=advisory_lock_id
        )

        db_pool = await self.get_db_pool(db_params=self.db_params)
        async with db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(acquire_advisory_lock_sql, (advisory_lock_id,))

                result = await cursor.fetchone()
                return result[0] if result else False

    async def delete_message_returning_message(self, message_id: int) -> tuple[bytes] | None:
        """Deletes a message from the database and returns the message"""
        delete_message_returning_message_sql = sql.SQL(
            "DELETE FROM {table} WHERE id=%s RETURNING message"
        ).format(table=sql.Identifier(MESSAGE_TABLE))

        db_pool = await self.get_db_pool(db_params=self.db_params)
        async with db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(delete_message_returning_message_sql, (message_id,))

                return await cursor.fetchone()

    async def delete_channel_group(self, group_key: str, channel: str) -> None:
        """Deletes a channel from a group"""
        await GroupChannel.objects.filter(group_key=group_key, channel=channel).adelete()

    async def flush(self) -> None:
        """
        Flushes the channel layer by truncating the message and group tables
        """
        db_pool = await self.get_db_pool(db_params=self.db_params)
        async with db_pool.connection() as conn:
            await conn.execute(
                sql.SQL("TRUNCATE TABLE {table}").format(table=sql.Identifier(MESSAGE_TABLE))
            )
            await conn.execute(
                sql.SQL("TRUNCATE TABLE {table}").format(table=sql.Identifier(GROUP_CHANNEL_TABLE))
            )
