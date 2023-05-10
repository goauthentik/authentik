"""Make channels use custom Redis layer"""
import logging
import time
from asyncio import Lock, get_running_loop
from copy import deepcopy
from itertools import cycle
from urllib.parse import urlparse

from channels_redis.core import RedisChannelLayer
from channels_redis.utils import _wrap_close

from authentik.lib.utils.parser import (
    get_client,
    get_connection_pool,
    get_redis_options,
    process_config,
)

logger = logging.getLogger(__name__)


class CustomLoopLayer:
    """Custom Redis loop layer that creates new Redis connections"""

    def __init__(self, channel_layer):
        self._lock = Lock()
        self.channel_layer = channel_layer
        self._connections = {}

    def get_connection(self, index):
        """Get Redis connection"""
        if index not in self._connections:
            pool, client_config = get_connection_pool(
                self.channel_layer.config[index], use_async=True
            )
            self._connections[index] = get_client(client_config, pool)
            # Redis cluster does not support auto close of connection pools
            if hasattr(self._connections[index], "auto_close_connection_pool"):
                self._connections[index].auto_close_connection_pool = True

        return self._connections[index]

    async def flush(self):
        """Close all open connections"""
        async with self._lock:
            for index in list(self._connections):
                connection = self._connections.pop(index)
                await connection.close()


class CustomChannelLayer(RedisChannelLayer):
    """
    Custom Redis channel layer to allow for full Redis client support

    It routes all messages into remote Redis server. Support for
    sharding among different Redis installations and message
    encryption are provided.
    """

    def __init__(self, url=None, **kwargs):
        url = urlparse(url)
        # Since RedisChannelLayer is using BRPOP we disable socket timeout
        # https://github.com/redis/redis-py/issues/583
        config = process_config(url, *get_redis_options(url, disable_socket_timeout=True))
        self.config = [config]
        if config["type"] == "sentinel":
            config_slave = deepcopy(config)
            config_slave["is_slave"] = True
            self.config.append(config_slave)
        super().__init__([], **kwargs)
        self._receive_index_generator = cycle(range(self.ring_size))
        self._send_index_generator = cycle(range(self.ring_size))

    @property
    def ring_size(self):
        """Return number of open connections"""
        return len(self.config)

    @ring_size.setter
    def ring_size(self, value):
        """Do not allow setting number of open connections"""
        return

    def connection(self, index):
        """
        Returns the correct connection for the index given.
        Lazily instantiates pools.
        """
        # Catch bad indexes

        if not 0 <= index < self.ring_size:
            raise ValueError(f"There are only {self.ring_size} hosts - you asked for {index}!")

        loop = get_running_loop()
        try:
            layer = self._layers[loop]
        except KeyError:
            _wrap_close(self, loop)
            layer = self._layers[loop] = CustomLoopLayer(self)

        return layer.get_connection(index)

    async def _brpop_with_clean(self, index, channel, timeout):
        """
        Perform a Redis BRPOP and manage the backup processing queue.
        In case of cancellation, make sure the message is not lost.
        """

        backup_queue = self._backup_channel_name(channel)
        connection = self.connection(index)
        # We pop messages from the processing queue and push them in front
        # of the main message queue in the proper order; BRPOP must *not* be called
        # because that would deadlock the server
        backed_up = await connection.zrange(backup_queue, 0, -1, withscores=True)
        for i in range(len(backed_up) - 1, -1, -2):
            await connection.zadd(channel, {backed_up[i - 1]: float(backed_up[i])})
        await connection.delete(backup_queue)
        result = await connection.bzpopmin(channel, timeout=timeout)

        if result is not None:
            _, member, timestamp = result
            await connection.zadd(backup_queue, {member: float(timestamp)})
        else:
            member = None

        return member

    async def flush(self):
        """
        Deletes all messages and groups on all shards.
        """
        # Make sure all channel cleaners have finished before removing
        # keys from under their feet.
        await self.wait_received()

        # Go through each connection and remove all with prefix
        for i in range(self.ring_size):
            connection = self.connection(i)
            keys = await connection.keys(self.prefix + "*")
            for j in range(0, len(keys), 5000):
                await connection.delete(*keys[j : j + 5000])
        # Now clear the pools as well
        await self.close_pools()

    async def group_send(self, group, message):
        """
        Sends a message to the entire group.
        """
        if not self.valid_group_name(group):
            raise ValueError("Group name not valid")
        # Retrieve list of all channel names
        key = self._group_key(group)
        connection = self.connection(self.consistent_hash(group))
        # Discard old channels based on group_expiry
        await connection.zremrangebyscore(key, min=0, max=int(time.time()) - self.group_expiry)

        channel_names = [x.decode("utf8") for x in await connection.zrange(key, 0, -1)]

        (
            connection_to_channel_keys,
            channel_keys_to_message,
            channel_keys_to_capacity,
        ) = self._map_channel_keys_to_connection(channel_names, message)

        for connection_index, channel_redis_keys in connection_to_channel_keys.items():
            # Discard old messages based on expiry
            pipe = connection.pipeline()
            for key in channel_redis_keys:
                pipe.zremrangebyscore(key, min=0, max=int(time.time()) - int(self.expiry))
            await pipe.execute()

            # channel_keys does not contain a single redis key more than once
            connection = self.connection(connection_index)

            channels_over_capacity = 0
            for key in channel_redis_keys:
                if await connection.zcount(key, "-inf", "inf") < channel_keys_to_capacity[key]:
                    await connection.zadd(key, time.time(), channel_keys_to_message[key])
                    await connection.expire(key, self.expiry)
                else:
                    channels_over_capacity += 1

            if channels_over_capacity > 0:
                logger.info(
                    "%s of %s channels over capacity in group %s",
                    channels_over_capacity,
                    len(channel_names),
                    group,
                )
