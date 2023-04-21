from asyncio import get_running_loop, Lock
from copy import deepcopy
from urllib.parse import urlparse

from channels_redis.core import RedisChannelLayer
from channels_redis.utils import _wrap_close

from authentik.lib.utils.parser import get_client, get_redis_options, process_config


class CustomLoopLayer:
    def __init__(self, channel_layer):
        self._lock = Lock()
        self.channel_layer = channel_layer
        self._connections = {}

    def get_connection(self, index):
        if index not in self._connections:
            self._connections[index] = get_client(self.channel_layer.config[index], use_async=True)
            if hasattr(self._connections[index], "auto_close_connection_pool"):
                self._connections[index].auto_close_connection_pool = True

        return self._connections[index]

    async def flush(self):
        async with self._lock:
            for index in list(self._connections):
                connection = self._connections.pop(index)
                await connection.close()


class CustomChannelLayer(RedisChannelLayer):
    def __init__(
        self,
        url=None,
        prefix="asgi",
        expiry=60,
        group_expiry=86400,
        capacity=100,
        channel_capacity=None,
        symmetric_encryption_keys=None,
    ):
        url = urlparse(url)
        config = process_config(url, *get_redis_options(url))
        self.config = [config]
        if config["type"] == "sentinel":
            config_slave = deepcopy(config)
            config_slave["is_slave"] = True
            self.config.append(config_slave)
        super().__init__([], prefix, expiry, group_expiry, capacity, channel_capacity,
                         symmetric_encryption_keys)

    @property
    def ring_size(self):
        return len(self.config)

    @ring_size.setter
    def ring_size(self, value):
        return

    def connection(self, index):
        """
        Returns the correct connection for the index given.
        Lazily instantiates pools.
        """
        # Catch bad indexes

        if not 0 <= index < self.ring_size:
            raise ValueError(
                f"There are only {self.ring_size} hosts - you asked for {index}!"
            )

        loop = get_running_loop()
        try:
            layer = self._layers[loop]
        except KeyError:
            _wrap_close(self, loop)
            layer = self._layers[loop] = CustomLoopLayer(self)

        return layer.get_connection(index)
