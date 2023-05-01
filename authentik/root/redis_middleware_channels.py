"""Make channels use custom Redis layer"""
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


class CustomLoopLayer:
    """Custom Redis loop layer that creates new Redis connections"""

    def __init__(self, channel_layer):
        self._lock = Lock()
        self.channel_layer = channel_layer
        self._connections = {}

    def get_connection(self, index):
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

    def __init__(
        self,
        url=None,
        **kwargs
    ):
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
