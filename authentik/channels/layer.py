import asyncio
from uuid import uuid4

import msgpack
from asgiref.sync import sync_to_async
from channels.layers import BaseChannelLayer
from django.db import connections, transaction
from django.utils.timezone import now, timedelta
from psycopg import sql

from authentik.channels.models import GroupChannel, Message


class PostgresChannelLayer(BaseChannelLayer):
    def __init__(
        self,
        prefix="asgi",
        expiry=60,
        capacity=100,
        channel_capacity=None,
        group_expiry=86400,
        db_alias="default",
    ):
        self.expiry = expiry
        self.capacity = capacity
        self.channel_capacity = self.compile_capacities(channel_capacity or {})
        self.group_expiry = group_expiry
        self.prefix = prefix
        self.client_prefix = uuid4().hex
        self.db_alias = db_alias

    # Channel layer API

    extensions = ["groups", "flush"]

    def _channel_key(self, channel):
        """
        Common function to make the storage key for the channel.
        """
        return f"{self.prefix}:channel:{self.non_local_name(channel)}"

    async def send(self, channel, message):
        """
        Send a message onto a (general or specific) channel.
        """
        # Typecheck
        assert isinstance(message, dict), "message is not a dict"  # nosec
        assert self.valid_channel_name(channel), "Channel name not valid"  # nosec
        # Make sure the message does not contain reserved keys
        assert "__asgi_channel__" not in message  # nosec
        # If it's a process-local channel, strip off local part and stick full name in message
        if "!" in channel:
            message = dict(message.items())
            message["__asgi_channel__"] = channel

        message = self.serialize(message)

        await Message.objects.using(self.db_alias).acreate(
            channel_key=self._channel_key(channel),
            message=message,
            expire=now() + timedelta(seconds=self.expiry),
        )

    def _receive_via_listen(self, channel_key) -> str | None:
        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(sql.SQL("LISTEN {}").format(sql.Identifier(channel_key)))
            notifies = list(cursor.connection.notifies(stop_after=1, timeout=5))
            if notifies:
                return notifies[0].payload
        return None

    def _receive_backlog(self, channel_key) -> Message | None:
        with transaction.atomic(using=self.db_alias):
            message = (
                Message.objects.using(self.db_alias)
                .select_for_update(skip_locked=True)
                .filter(
                    channel_key=channel_key,
                    expire__gte=now(),
                )
                .order_by("created_at")
                .first()
            )
            if message:
                message.delete(using=self.db_alias)
                return message
        return None

    def _receive_with_id(self, message_id) -> Message:
        with transaction.atomic(using=self.db_alias):
            message = (
                Message.objects.using(self.db_alias)
                .select_for_update(skip_locked=True)
                .filter(pk=message_id)
                .first()
            )
            if message:
                message.delete(using=self.db_alias)
                return message
        return None

    async def _receive_single(self, channel_key) -> Message:
        message = None
        while message is None:
            message = await sync_to_async(self._receive_backlog)(channel_key)
            if message:
                return message
            message_id = None
            while message_id is None:
                message_id = await sync_to_async(self._receive_via_listen)(channel_key)
            message = await sync_to_async(self._receive_with_id)(message_id)
        return message

    async def receive(self, channel):
        """
        Receive the first message that arrives on the channel.
        If more than one coroutine waits on the same channel, the first waiter
        will be given the message when it arrives.
        """
        assert self.valid_channel_name(channel)  # nosec

        channel_key = f"{self.prefix}.{self.non_local_name(channel)}"

        message = await self._receive_single(channel_key)

        message = self.deserialize(message.message)
        if "__asgi_channel__" in message:
            channel = message["__asgi_channel__"]
            del message["__asgi_channel__"]

        return channel, message

    async def new_channel(self, prefix="specific"):
        """
        Returns a new channel name that can be used by something in our
        process as a specific channel.
        """
        return f"{prefix}.{self.client_prefix}!{uuid4().hex}"

    # Flush extension

    async def flush(self):
        """
        Deletes all messages and groups in the database

        This doesn't flush Postgres' NOTIFY queue
        Postgres doesn't provide access to this table/queue.
        """
        await GroupChannel.objects.using(self.db_alias).all().adelete()
        await Message.objects.using(self.db_alias).all().adelete()

    # Groups extension

    def _group_key(self, group):
        """
        Common function to make the storage key for the group.
        """
        return f"{self.prefix}:group:{group}"

    async def group_add(self, group, channel):
        """
        Adds the channel name to a group.
        """
        assert self.valid_group_name(group), "Group name not valid"  # nosec
        assert self.valid_channel_name(channel), "Channel name not valid"  # nosec

        group_key = self._group_key(group)

        await GroupChannel.objects.using(self.db_alias).acreate(
            group_key=group_key,
            channel=channel,
            expire=now() + timedelta(seconds=self.group_expiry),
        )

    async def group_discard(self, group, channel):
        """
        Removes the channel from the named group if it is in the group;
        does nothing otherwise (does not error)
        """
        assert self.valid_group_name(group), "Group name not valid"  # nosec
        assert self.valid_channel_name(channel), "Channel name not valid"  # nosec

        group_key = self._group_key(group)

        await (
            GroupChannel.objects.using(self.db_alias)
            .filter(group_key=group_key, channel=channel)
            .adelete()
        )

        if self.group_expiry > 0:
            asyncio.create_task(
                GroupChannel.objects.using(self.db_alias).filter(expire__lt=now()).adelete()
            )
        asyncio.create_task(Message.objects.using(self.db_alias).filter(expire__lt=now()).adelete())

    async def group_send(self, group, message):
        """
        Sends a message to the entire group.
        """
        assert self.valid_group_name(group), "Group name not valid"  # nosec

        group_key = self._group_key(group)

        sends = []
        async for group_channel in GroupChannel.objects.using(self.db_alias).filter(
            group_key=group_key,
            expire__gte=now(),
        ):
            sends.append(self.send(group_channel.channel, message))
        await asyncio.gather(*sends)

    # Serialization

    def serialize(self, message):
        return msgpack.packb(message, use_bin_type=True)

    def deserialize(self, message):
        return msgpack.unpackb(message, raw=False)
